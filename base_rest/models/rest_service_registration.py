# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""

REST Service Registy Builder
============================

Register available REST services at the build of a registry.

This code is inspired by ``odoo.addons.component.builder.ComponentBuilder``

"""
import inspect

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
)
from ..tools import _inspect_methods


class RestServiceRegistation(models.AbstractModel):
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
        controllers = http.controllers_per_module["base_rest"]
        controllers = [
            (name, cls) for name, cls in controllers if "RestController" not in name
        ]
        http.controllers_per_module["base_rest"] = controllers
        # create the final controller providing the http routes for
        # the services available into the current database
        self._build_controllers_routes(services_registry)

    def _build_controllers_routes(self, services_registry):
        for controller_def in services_registry.values():
            for service in self._get_services(controller_def["collection_name"]):
                RestApiMethodTransformer(service, controller_def).fix()
                self._build_controller(service, controller_def)

    def _build_controller(self, service, controller_def):
        base_controller_cls = controller_def["controller_class"]
        # build our new controller class
        ctrl_cls = RestApiServiceControllerGenerator(
            service, base_controller_cls
        ).generate()

        # generate an addon name used to register our new controller for
        # the current database
        addon_name = "{}_{}_{}".format(
            self.env.cr.dbname,
            service._collection.replace(".", "_"),
            service._usage.replace(".", "_"),
        )
        # put our new controller into the new addon module
        ctrl_cls.__module__ = "odoo.addons.{}".format(addon_name)

        # instruct the registry that our fake addon is part of the loaded
        # modules
        self.env.registry._init_modules.add(addon_name)

        # register our conroller into the list of available controllers
        name_class = ("{}.{}".format(ctrl_cls.__module__, ctrl_cls.__name__), ctrl_cls)
        http.controllers_per_module[addon_name].append(name_class)

    def _get_services(self, collection_name):
        collection = _PseudoCollection(collection_name, self.env)
        work = WorkContext(
            model_name="rest.service.registration", collection=collection
        )
        component_classes = work._lookup_components(usage=None, model_name=None)
        # removes component without collection that are not a rest service
        component_classes = [
            c
            for c in component_classes
            if c._collection and issubclass(c, BaseRestService)
        ]
        return [comp(work) for comp in component_classes]

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
            services_registry[controller_def["root_path"]] = controller_def

    def _init_global_registry(self):
        services_registry = RestServicesRegistry()
        _rest_services_databases[self.env.cr.dbname] = services_registry
        return services_registry


class RestApiMethodTransformer(object):
    """Helper class to generate and apply the missing restapi.method decorator
    to service's methods defined without decorator.

    Before 10/12.0.3.0.0 methods exposed by a service was based on implicit
    conventions. This transformer is used to keep this functionality by
    generating and applying the missing decorators. As result all the methods
    exposed are decorated and the processing can be based on these decorators.
    """

    def __init__(self, service, controller_def):
        self._service = service
        self._controller_class = controller_def["controller_class"]

    def fix(self):
        methods_to_fix = []
        for name, method in _inspect_methods(self._service.__class__):
            if not self._is_public_api_method(name):
                continue
            if not hasattr(method, "routing"):
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
        auth = self._method_to_auth(method)
        decorated_method = restapi.method(
            routes=routes, input_param=input_param, output_param=output_param, auth=auth
        )(getattr(self._service.__class__, method_name))
        setattr(self._service.__class__, method_name, decorated_method)

    def _method_to_auth(self, method):
        method_name = method.__name__
        auth = self._controller_class._default_auth
        if method_name in self._controller_class._auth_by_method:
            auth = self._controller_class._auth_by_method[method_name]
        return auth

    def _method_to_routes(self, method):
        """
        Generate the restapi.method's routes
        :param method:
        :return: A list of routes used to get access to the method
        """
        method_name = method.__name__
        signature = inspect.signature(method)
        id_in_path_required = "_id" in signature.parameters
        path = "/{}".format(method_name)
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
        validator_method_name = "_validator_{}".format(method.__name__)
        return self._method_to_param(validator_method_name, "input")

    def _method_to_output_param(self, method):
        validator_method_name = "_validator_return_{}".format(method.__name__)
        return self._method_to_param(validator_method_name, "output")


class RestApiServiceControllerGenerator(object):
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
        return type(
            self._new_cls_name, (self._base_controller,), self._generate_methods()
        )

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
        root_path = "{}{}{}".format(root_path, path_sep, self._service._usage)
        for name, method in _inspect_methods(self._service.__class__):
            if not hasattr(method, "routing"):
                continue
            routing = method.routing
            for routes, http_method in routing["routes"]:
                method_name = "{}_{}".format(http_method.lower(), name)
                default_route = routes[0]
                rule = Rule(default_route)
                Map(rules=[rule])
                if rule.arguments:
                    method = METHOD_TMPL_WITH_ARGS.format(
                        method_name=method_name,
                        service_name=self._service_name,
                        service_method_name=name,
                        args=", ".join(rule.arguments),
                    )
                else:
                    method = METHOD_TMPL.format(
                        method_name=method_name,
                        service_name=self._service_name,
                        service_method_name=name,
                    )
                exec(method, _globals)
                method_exec = _globals[method_name]
                method_exec = http.route(
                    ["{}{}".format(root_path, r) for r in routes],
                    methods=[http_method],
                    auth=routing["auth"],
                    cors=routing["cors"],
                    csrf=routing["csrf"],
                )(method_exec)
                methods[method_name] = method_exec
        return methods


METHOD_TMPL = """
def {method_name}(self, **kwargs):
    return self._process_method(
        "{service_name}",
        "{service_method_name}",
        params=kwargs
    )
"""


METHOD_TMPL_WITH_ARGS = """
def {method_name}(self, {args}, **kwargs):
    return self._process_method(
        "{service_name}",
        "{service_method_name}",
        *[{args}],
        params=kwargs
    )
"""
