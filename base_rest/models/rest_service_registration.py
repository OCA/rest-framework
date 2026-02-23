# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""

REST Service Registy Builder
============================

Register available REST services at the build of a registry.

This code is inspired by ``odoo.addons.component.builder.ComponentBuilder``

"""

import inspect
import logging

from werkzeug.routing import Map, Rule

import odoo
from odoo import http, models

from odoo.addons.component.core import WorkContext

from .. import restapi
from ..components.service import BaseRestService
from ..controllers.main import _PseudoCollection
from ..core import (
    RestServicesRegistry,
    _rest_controllers_per_module,
    _rest_services_databases,
    _rest_services_routes,
)
from ..tools import ROUTING_DECORATOR_ATTR, _inspect_methods

_logger = logging.getLogger(__name__)


class RestServiceRegistration(models.AbstractModel):
    """Register REST services into the REST services registry

    This class allows us to hook the registration of the root urls of all
    the REST controllers installed into the current database at the end of the
    Odoo's registry loading, using ``_register_hook``. This method is called
    after all modules are loaded, so we are sure that we only register REST
    services installed into the current database.

    """

    _name = "rest.service.registration"
    _description = "REST Services Registration Model"

    def _register_hook(self):
        # This method is called by Odoo when the registry is built,
        # so in case the registry is rebuilt (cache invalidation, ...),
        # we have to to rebuild the registry. We use a new
        # registry so we have an empty cache and we'll add services in it.
        services_registry = self._init_global_registry()
        self.build_registry(services_registry)
        # we also have to remove the RestController from the
        # controller_per_module registry since it's an abstract controller
        controllers = http.Controller.children_classes["base_rest"]
        controllers = [
            cls for cls in controllers if "RestController" not in cls.__name__
        ]
        http.Controller.children_classes["base_rest"] = controllers
        # create the final controller providing the http routes for
        # the services available into the current database
        self._build_controllers_routes(services_registry)

    def _build_controllers_routes(self, services_registry):
        for controller_def in services_registry.values():
            for service in self._get_services(controller_def["collection_name"]):
                self._prepare_non_decorated_endpoints(service)
                self._build_controller(service, controller_def)

    def _prepare_non_decorated_endpoints(self, service):
        # Autogenerate routing info where missing
        RestApiMethodTransformer(service).fix()

    def _build_controller(self, service, controller_def):
        _logger.debug("Build service %s for controller_def %s", service, controller_def)
        base_controller_cls = controller_def["controller_class"]
        # build our new controller class
        ctrl_cls = RestApiServiceControllerGenerator(
            service, base_controller_cls
        ).generate()

        # generate an addon name used to register our new controller for
        # the current database
        addon_name = base_controller_cls._module
        identifier = "{}_{}_{}".format(
            self.env.cr.dbname,
            service._collection.replace(".", "_"),
            service._usage.replace(".", "_"),
        )
        base_controller_cls._identifier = identifier
        # put our new controller into the new addon module
        ctrl_cls.__module__ = f"odoo.addons.{addon_name}"

        self.env.registry._init_modules.add(addon_name)

        # register our conroller into the list of available controllers
        http.Controller.children_classes[addon_name].append(ctrl_cls)
        self._apply_defaults_to_controller_routes(controller_class=ctrl_cls)

    def _apply_defaults_to_controller_routes(self, controller_class):
        """
        Apply default routes properties defined on the controller_class to
        routes where properties are missing
        Set the automatic auth on controller's routes.

        During definition of new controller, the _default_auth should be
        applied on every routes (cfr @route odoo's decorator).
        This auth attribute should be applied only if the route doesn't already
        define it.
        :return:
        """
        for _name, method in _inspect_methods(controller_class):
            routing = getattr(method, ROUTING_DECORATOR_ATTR, None)
            if not routing:
                continue
            self._apply_default_auth_if_not_set(controller_class, routing)
            self._apply_default_if_not_set(controller_class, routing, "csrf")
            self._apply_default_if_not_set(controller_class, routing, "save_session")
            self._apply_default_cors_if_not_set(controller_class, routing)

    def _apply_default_if_not_set(self, controller_class, routing, attr_name):
        default_attr_name = "_default_" + attr_name
        if hasattr(controller_class, default_attr_name) and attr_name not in routing:
            routing[attr_name] = getattr(controller_class, default_attr_name)

    def _apply_default_auth_if_not_set(self, controller_class, routing):
        default_attr_name = "_default_auth"
        default_auth = getattr(controller_class, default_attr_name, None)
        if default_auth:
            if "auth" in routing:
                auth = routing["auth"]
                if auth == "public_or_default":
                    alternative_auth = "public_or_" + default_auth
                    if getattr(
                        self.env["ir.http"], f"_auth_method_{alternative_auth}", None
                    ):
                        routing["auth"] = alternative_auth
                    else:
                        _logger.debug(
                            "No %s auth method available: Fallback on %s",
                            alternative_auth,
                            default_auth,
                        )
                        routing["auth"] = default_auth
            else:
                routing["auth"] = default_auth

    def _apply_default_cors_if_not_set(self, controller_class, routing):
        default_attr_name = "_default_cors"
        if hasattr(controller_class, default_attr_name) and "cors" not in routing:
            cors = getattr(controller_class, default_attr_name)
            routing["cors"] = cors
            if cors and "OPTIONS" not in routing.get("methods", ["OPTIONS"]):
                # add http method 'OPTIONS' required by cors if the route is
                # restricted to specific method
                routing["methods"].append("OPTIONS")

    def _get_services(self, collection_name):
        collection = _PseudoCollection(collection_name, self.env)
        work = WorkContext(
            model_name="rest.service.registration", collection=collection
        )
        component_classes = work._lookup_components(usage=None, model_name=None)
        # removes component without collection that are not a rest service
        component_classes = [
            c for c in component_classes if self._filter_service_component(c)
        ]
        return [comp(work) for comp in component_classes]

    @staticmethod
    def _filter_service_component(comp):
        return (
            issubclass(comp, BaseRestService)
            and comp._collection
            and comp._usage
            and getattr(comp, "_is_rest_service_component", True)
        )

    def build_registry(self, services_registry, states=None, exclude_addons=None):
        if not states:
            states = ("installed", "to upgrade")
        # we load REST, controllers following the order of the 'addons'
        # dependencies to ensure that controllers defined in a more
        # specialized addon and overriding more generic one takes precedences
        # on the generic one into the registry
        graph = odoo.modules.graph.Graph()
        graph.add_module(self.env.cr, "base")

        query = "SELECT name " "FROM ir_module_module " "WHERE state IN %s "
        params = [tuple(states)]
        if exclude_addons:
            query += " AND name NOT IN %s "
            params.append(tuple(exclude_addons))
        self.env.cr.execute(query, params)

        module_list = [name for (name,) in self.env.cr.fetchall() if name not in graph]
        graph.add_modules(self.env.cr, module_list)

        for module in graph:
            self.load_services(module.name, services_registry)

    def load_services(self, module, services_registry):
        controller_defs = _rest_controllers_per_module.get(module, [])
        for controller_def in controller_defs:
            root_path = controller_def["root_path"]
            is_base_contoller = not getattr(
                controller_def["controller_class"], "_generated", False
            )
            if is_base_contoller:
                current_controller = (
                    services_registry[root_path]["controller_class"]
                    if root_path in services_registry
                    else None
                )
                services_registry[controller_def["root_path"]] = controller_def
                self._register_rest_route(controller_def["root_path"])
                if (
                    current_controller
                    and current_controller != controller_def["controller_class"]
                ):
                    _logger.error(
                        "Only one REST controller can be safely declared for root "
                        "path %s\n "
                        "Registering controller %s\n "
                        "Registered controller%s\n",
                        root_path,
                        controller_def,
                        services_registry[controller_def["root_path"]],
                    )

    def _init_global_registry(self):
        services_registry = RestServicesRegistry()
        _rest_services_databases[self.env.cr.dbname] = services_registry
        return services_registry

    def _register_rest_route(self, route_path):
        """Register given route path to be handles as RestRequest.

        See base_rest.http.get_request.
        """
        _rest_services_routes[self.env.cr.dbname].add(route_path)


class RestApiMethodTransformer:
    """Helper class to generate and apply the missing restapi.method decorator
    to service's methods defined without decorator.

    Before 10/12.0.3.0.0 methods exposed by a service was based on implicit
    conventions. This transformer is used to keep this functionality by
    generating and applying the missing decorators. As result all the methods
    exposed are decorated and the processing can be based on these decorators.
    """

    def __init__(self, service):
        self._service = service

    def fix(self):
        methods_to_fix = []
        for name, method in _inspect_methods(self._service.__class__):
            if not self._is_public_api_method(name):
                continue
            if not hasattr(method, ROUTING_DECORATOR_ATTR):
                methods_to_fix.append(method)
        for method in methods_to_fix:
            self._fix_method_decorator(method)

    def _is_public_api_method(self, method_name):
        if method_name.startswith("_"):
            return False
        if not hasattr(self._service, method_name):
            return False
        if hasattr(BaseRestService, method_name):
            # exclude methods from base class
            return False
        return True

    def _fix_method_decorator(self, method):
        method_name = method.__name__
        routes = self._method_to_routes(method)
        input_param = self._method_to_input_param(method)
        output_param = self._method_to_output_param(method)
        decorated_method = restapi.method(
            routes=routes, input_param=input_param, output_param=output_param
        )(getattr(self._service.__class__, method_name))
        setattr(self._service.__class__, method_name, decorated_method)

    def _method_to_routes(self, method):
        """
        Generate the restapi.method's routes
        :param method:
        :return: A list of routes used to get access to the method
        """
        method_name = method.__name__
        signature = inspect.signature(method)
        id_in_path_required = "_id" in signature.parameters
        path = f"/{method_name}"
        if id_in_path_required:
            path = "/<int:id>" + path
        if method_name in ("get", "search"):
            paths = [path]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            paths.append(path)
            return [(paths, "GET")]
        elif method_name == "delete":
            routes = [(path, "POST")]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            routes.append((path, "DELETE"))
        elif method_name == "update":
            paths = [path]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            paths.append(path)
            routes = [(paths, "POST"), (path, "PUT")]
        elif method_name == "create":
            paths = [path]
            path = "/"
            if id_in_path_required:
                path = "/<int:id>"
            paths.append(path)
            routes = [(paths, "POST")]
        else:
            routes = [(path, "POST")]

        return routes

    def _method_to_param(self, validator_method_name, direction):
        validator_component = self._service.component(usage="cerberus.validator")
        if validator_component.has_validator_handler(
            self._service, validator_method_name, direction
        ):
            return restapi.CerberusValidator(schema=validator_method_name)
        return None

    def _method_to_input_param(self, method):
        validator_method_name = f"_validator_{method.__name__}"
        return self._method_to_param(validator_method_name, "input")

    def _method_to_output_param(self, method):
        validator_method_name = f"_validator_return_{method.__name__}"
        return self._method_to_param(validator_method_name, "output")


class RestApiServiceControllerGenerator:
    """
    An object helper used to generate the http.Controller required to serve
    the method decorated with the `@restappi.method` decorator
    """

    def __init__(self, service, base_controller):
        self._service = service
        self._service_name = service._usage
        self._base_controller = base_controller

    @property
    def _new_cls_name(self):
        controller_name = self._base_controller.__name__
        return "{}{}".format(
            controller_name, self._service._usage.title().replace(".", "_")
        )

    def generate(self):
        """
        :return: A new controller child of base_controller defining the routes
        required to serve the method of the services.
        """
        controller = type(
            self._new_cls_name, (self._base_controller,), self._generate_methods()
        )
        controller._generated = True
        return controller

    def _generate_methods(self):
        """Generate controller's methods and associated routes

        This method inspect the service definition and generate the appropriate
        methods and routing rules for all the methods decorated with @restappi.method
        :return: A dictionary of method name : method
        """
        methods = {}
        _globals = {}
        root_path = self._base_controller._root_path
        path_sep = ""
        if root_path[-1] != "/":
            path_sep = "/"
        root_path = f"{root_path}{path_sep}{self._service._usage}"
        for name, method in _inspect_methods(self._service.__class__):
            routing = getattr(method, ROUTING_DECORATOR_ATTR, None)
            if routing is None:
                continue
            for routes, http_method in routing["routes"]:
                method_name = f"{http_method.lower()}_{name}"
                default_route = routes[0]
                rule = Rule(default_route)
                Map(rules=[rule])
                if rule.arguments:
                    method = METHOD_TMPL_WITH_ARGS.format(
                        method_name=method_name,
                        service_name=self._service_name,
                        service_method_name=name,
                        args=", ".join([c[1] for c in rule._trace if c[0]]),
                    )
                else:
                    method = METHOD_TMPL.format(
                        method_name=method_name,
                        service_name=self._service_name,
                        service_method_name=name,
                    )
                exec(method, _globals)
                method_exec = _globals[method_name]
                route_params = dict(
                    route=[f"{root_path}{r}" for r in routes],
                    methods=[http_method],
                    type="restapi",
                )
                for attr in {"auth", "cors", "csrf", "save_session"}:
                    if attr in routing:
                        route_params[attr] = routing[attr]
                method_exec = http.route(**route_params)(method_exec)
                methods[method_name] = method_exec
        return methods


METHOD_TMPL = """
def {method_name}(self, collection=None, **kwargs):
    return self._process_method(
        "{service_name}",
        "{service_method_name}",
        collection=collection,
        params=kwargs
    )
"""


METHOD_TMPL_WITH_ARGS = """
def {method_name}(self, {args}, collection=None, **kwargs):
    return self._process_method(
        "{service_name}",
        "{service_method_name}",
        *[{args}],
        collection=collection,
        params=kwargs
    )
"""
