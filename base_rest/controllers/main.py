# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import inspect
import logging
from contextlib import contextmanager
from urllib.parse import urljoin

from werkzeug.exceptions import BadRequest

from odoo.http import Controller, ControllerType, Response, request, route

from odoo.addons.component.core import WorkContext, _get_addon_name

from ..core import _rest_controllers_per_module

_logger = logging.getLogger(__name__)


class _PseudoCollection(object):
    __slots__ = "_name", "env"

    def __init__(self, name, env):
        self._name = name
        self.env = env


class RestControllerType(ControllerType):

    # pylint: disable=E0213
    def __init__(cls, name, bases, attrs):  # noqa: B902
        if (
            "RestController" in globals()
            and RestController in bases
            and Controller not in bases
        ):
            # to be registered as a controller into the ControllerType,
            # our RestConrtroller must be a direct child of Controller
            bases += (Controller,)
        super(RestControllerType, cls).__init__(name, bases, attrs)
        if "RestController" not in globals() or RestController not in bases:
            return
        # register the rest controller into the rest controllers registry
        root_path = getattr(cls, "_root_path", None)
        collection_name = getattr(cls, "_collection_name", None)
        if root_path and collection_name:
            if not hasattr(cls, "_module"):
                cls._module = _get_addon_name(cls.__module__)
            _rest_controllers_per_module[cls._module].append(
                {"root_path": root_path, "collection_name": collection_name}
            )

    @classmethod
    def _add_default_methods(cls, bases, members):
        if "RestController" in globals() and RestController in bases:

            @route(
                [
                    "<string:_service_name>",
                    "<string:_service_name>/search",
                    "<string:_service_name>/<int:_id>",
                    "<string:_service_name>/<int:_id>/get",
                ],
                methods=["GET"],
            )
            def get(self, _service_name, _id=None, **params):
                method_name = "get" if _id else "search"
                return self._process_method(_service_name, method_name, _id, params)

            @route(
                [
                    "<string:_service_name>",
                    "<string:_service_name>/<string:method_name>",
                    "<string:_service_name>/<int:_id>",
                    "<string:_service_name>/<int:_id>/<string:method_name>",
                ],
                methods=["POST"],
            )
            def modify(self, _service_name, _id=None, method_name=None, **params):
                if not method_name:
                    method_name = "update" if _id else "create"
                if method_name == "get":
                    _logger.error(
                        "HTTP POST with method name 'get' is not allowed. "
                        "(service name: %s)",
                        _service_name,
                    )
                    raise BadRequest()
                return self._process_method(_service_name, method_name, _id, params)

            @route(["<string:_service_name>/<int:_id>"], methods=["PUT"])
            def update(self, _service_name, _id, **params):
                return self._process_method(_service_name, "update", _id, params)

            @route(["<string:_service_name>/<int:_id>"], methods=["DELETE"])
            def delete(self, _service_name, _id):
                return self._process_method(_service_name, "delete", _id)

            members.update(
                {"get": get, "modify": modify, "update": update, "delete": delete}
            )

    @classmethod
    def _prepend_route_path(cls, klass):
        """Add the root path to all the route defined by the controller"""
        if not klass._root_path:
            return
        # Add the root_path to the routes defined into the controller
        for member in inspect.getmembers(klass, predicate=inspect.isfunction):
            method = member[1]
            if (
                not hasattr(method, "original_func")
                or "rest_routes_patched" in method.routing
            ):
                continue
            routing = method.routing
            routes = routing.get("routes")
            patched_routes = []
            for _route in routes:
                patched_routes.append(urljoin(klass._root_path, _route))
            routing["routes"] = patched_routes
            methods = routing["methods"]
            if "auth" not in routing:
                auth = klass._default_auth
                if len(methods) == 1:
                    method = methods[0]
                    if method in klass._auth_by_method:
                        auth = klass._auth_by_method[method]
                routing["auth"] = auth
            if "cors" not in routing:
                routing["cors"] = klass._cors
            if "csrf" not in routing:
                routing["csrf"] = klass._csrf
            routing["rest_routes_patched"] = True

    def __new__(cls, name, bases, members):
        # concrete RestController Factory
        RestControllerType._add_default_methods(bases, members)
        # we create our concrete controller
        klass = type.__new__(cls, name, bases, members)
        RestControllerType._prepend_route_path(klass)
        return klass


class RestController(Controller, metaclass=RestControllerType):
    """Generic REST Controller

    This controller provides generic routes conform to commen REST usages.
    You must inherit of this controller into your code to register your REST
    routes. At the same time you must fill 2 required informations:

    _root_path:
    _collection_name:

    """

    _root_path = None
    _collection_name = None
    # The default authentication to apply to all pre defined routes.
    _default_auth = "user"
    # You can use this parameter to specify an authentication method by HTTP
    # method ie: {'GET': None, 'POST': 'user'}
    _auth_by_method = {}
    # The default The Access-Control-Allow-Origin cors directive value.
    _cors = None
    # Whether CSRF protection should be enabled for the route.
    _csrf = False

    def _get_component_context(self):
        """
        This method can be inherited to add parameter into the component
        context
        :return: dict of key value.
        """
        return {"request": request}

    def make_response(self, data):
        if isinstance(data, Response):
            # The response has been build by the called method...
            return data
        # By default return result as json
        return request.make_json_response(data)

    @property
    def collection_name(self):
        return self._collection_name

    @property
    def collection(self):
        return _PseudoCollection(self.collection_name, request.env)

    @contextmanager
    def work_on_component(self):
        """
        Return the component that implements the methods of the requested
        service.
        :param service_name:
        :return: an instance of base.rest.service component
        """
        collection = self.collection
        params = self._get_component_context()
        yield WorkContext(
            model_name="rest.service.registration", collection=collection, **params
        )

    @contextmanager
    def service_component(self, service_name):
        """
        Return the component that implements the methods of the requested
        service.
        :param service_name:
        :return: an instance of base.rest.service component
        """
        with self.work_on_component() as work:
            service = work.component(usage=service_name)
            yield service

    def _validate_method_name(self, method_name):
        if method_name.startswith("_"):
            _logger.error(
                "REST API called with an unallowed method "
                "name: %s.\n Method can't start with '_'",
                method_name,
            )
            raise BadRequest()
        return True

    def _process_method(self, service_name, method_name, _id=None, params=None):
        self._validate_method_name(method_name)
        with self.service_component(service_name) as service:
            result = service.dispatch(method_name, _id, params)
            return self.make_response(result)
