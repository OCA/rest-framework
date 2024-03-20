# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from contextlib import contextmanager

from werkzeug.exceptions import BadRequest

from odoo import models
from odoo.http import Controller, Response, request

from odoo.addons.component.core import WorkContext, _get_addon_name

from ..core import _rest_controllers_per_module

_logger = logging.getLogger(__name__)


class _PseudoCollection:
    __slots__ = "_name", "env", "id"

    def __init__(self, name, env):
        self._name = name
        self.env = env
        self.id = None


class RestController(Controller):
    """Generic REST Controller

    This controller is the base controller used by as base controller for all the REST
    controller generated from the service components.

    You must inherit of this controller into your code to register the root path
    used to serve all the services defined for the given collection name.
    This registration requires 2 parameters:

    _root_path:
    _collection_name:

    Only one controller by _collection_name, _root_path should exists into an
    odoo database. If more than one controller exists, a warning is issued into
    the log at startup and the concrete controller used as base class
    for the services registered into the collection name and served at the
    root path is not predictable.

    Module A:
        class ControllerA(RestController):
            _root_path='/my_path/'
            _collection_name='my_services_collection'

    Module B depends A:                               A
        class ControllerB(ControllerA):             /  \
            pass                                   B    C
                                                  /
    Module C depends A:                          D
        class ControllerC(ControllerA):
            pass

    Module D depends B:
        class ControllerB(ControllerB):
            pass

    In the preceding illustration, services in module C will never be served
    by controller D or B. Therefore if the generic dispatch method is overridden
    in  B or D, this override wil never apply to services in C since in Odoo
    controllers are not designed to be inherited. That's why it's an error
    to have more than one controller registered for the same root path and
    collection name.

    The following properties can be specified to define common properties to
    apply to generated REST routes.

    _default_auth: The default authentication to apply to all pre defined routes.
                    default: 'user'
    _default_cors: The default Access-Control-Allow-Origin cors directive value.
                   default: None
    _default_csrf: Whether CSRF protection should be enabled for the route.
                   default: False
    _default_save_session: Whether session should be saved into the session store
                           default: True
    """

    _root_path = None
    _collection_name = None
    # The default authentication to apply to all pre defined routes.
    _default_auth = "user"
    # The default Access-Control-Allow-Origin cors directive value.
    _default_cors = None
    # Whether CSRF protection should be enabled for the route.
    _default_csrf = False
    # Whether session should be saved into the session store
    _default_save_session = True

    _component_context_provider = "component_context_provider"

    @classmethod
    def __init_subclass__(cls):
        if (
            "RestController" in globals()
            and RestController in cls.__bases__
            and Controller not in cls.__bases__
        ):
            # Ensure that Controller's __init_subclass__ kicks in.
            cls.__bases__ += (Controller,)
        super().__init_subclass__()
        if "RestController" not in globals() or not any(
            issubclass(b, RestController) for b in cls.__bases__
        ):
            return
        # register the rest controller into the rest controllers registry
        root_path = getattr(cls, "_root_path", None)
        collection_name = getattr(cls, "_collection_name", None)
        if root_path and collection_name:
            cls._module = _get_addon_name(cls.__module__)
            _rest_controllers_per_module[cls._module].append(
                {
                    "root_path": root_path,
                    "collection_name": collection_name,
                    "controller_class": cls,
                }
            )
            _logger.debug(
                "Added rest controller %s for module %s",
                _rest_controllers_per_module[cls._module][-1],
                cls._module,
            )

    def _get_component_context(self, collection=None):
        """
        This method can be inherited to add parameter into the component
        context
        :return: dict of key value.
        """
        work = WorkContext(
            model_name="rest.service.registration",
            collection=collection or self.default_collection,
            request=request,
            controller=self,
        )
        provider = work.component(usage=self._component_context_provider)
        return provider._get_component_context()

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
    def default_collection(self):
        return _PseudoCollection(self.collection_name, request.env)

    @contextmanager
    def work_on_component(self, collection=None):
        """
        Return the component that implements the methods of the requested
        service.
        :param service_name:
        :return: an instance of base.rest.service component
        """
        collection = collection or self.default_collection
        component_ctx = self._get_component_context(collection=collection)
        env = collection.env
        collection.env = env(
            context=dict(
                env.context,
                authenticated_partner_id=component_ctx.get("authenticated_partner_id"),
            )
        )
        yield WorkContext(model_name="rest.service.registration", **component_ctx)

    @contextmanager
    def service_component(self, service_name, collection=None):
        """
        Return the component that implements the methods of the requested
        service.
        :param service_name:
        :return: an instance of base.rest.service component
        """
        with self.work_on_component(collection=collection) as work:
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

    def _process_method(
        self, service_name, method_name, *args, collection=None, params=None
    ):
        self._validate_method_name(method_name)
        if isinstance(collection, models.Model) and not collection:
            raise request.not_found()
        with self.service_component(service_name, collection=collection) as service:
            result = service.dispatch(method_name, *args, params=params)
            return self.make_response(result)
