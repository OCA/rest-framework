# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2020 ACSONE SA/NV
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Laurent Mignon <laurent.mignon@acsone.eu>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import copy

from odoo import http
from odoo.tests.common import TransactionCase, get_db_name

from odoo.addons.component.core import (
    WorkContext,
    _component_databases,
    _get_addon_name,
)
from odoo.addons.component.tests.common import (
    ComponentRegistryCase,
    SavepointComponentCase,
    new_rollbacked_env,
)

from ..components.service import BaseRestService
from ..controllers.main import RestController, _PseudoCollection
from ..core import RestServicesRegistry, _rest_services_databases
from ..tools import _inspect_methods


class RegistryMixin(object):
    @classmethod
    def setUpRegistry(cls):
        with new_rollbacked_env() as env:
            service_registration = env["rest.service.registration"]
            # build the registry of every installed addons
            services_registry = service_registration._init_global_registry()
            cls._services_registry = services_registry
            # ensure that we load only the services of the 'installed'
            # modules, not 'to install', which means we load only the
            # dependencies of the tested addons, not the siblings or
            # children addons
            service_registration.build_registry(
                services_registry, states=("installed",)
            )
            # build the services of the current tested addon
            current_addon = _get_addon_name(cls.__module__)
            service_registration.load_services(current_addon, services_registry)
            env["rest.service.registration"]._build_controllers_routes(
                services_registry
            )


class RestServiceRegistryCase(ComponentRegistryCase):

    # pylint: disable=W8106
    @staticmethod
    def _setup_registry(class_or_instance):
        ComponentRegistryCase._setup_registry(class_or_instance)

        class_or_instance._service_registry = RestServicesRegistry()
        # take a copy of registered controllers
        controllers = http.controllers_per_module
        http.controllers_per_module = controllers

        class_or_instance._controllers_per_module = copy.deepcopy(
            http.controllers_per_module
        )
        db_name = get_db_name()

        # makes the test component registry available for the db name
        _component_databases[db_name] = class_or_instance.comp_registry

        # makes the test service registry available for the db name
        class_or_instance._original_services_registry = _rest_services_databases.get(
            db_name, {}
        )
        _rest_services_databases[db_name] = class_or_instance._service_registry

        # build the services and controller of every installed addons
        # but the current addon (when running with pytest/nosetest, we
        # simulate the --test-enable behavior by excluding the current addon
        # which is in 'to install' / 'to upgrade' with --test-enable).
        current_addon = _get_addon_name(class_or_instance.__module__)
        with new_rollbacked_env() as env:
            RestServiceRegistration = env["rest.service.registration"]
            RestServiceRegistration.build_registry(
                class_or_instance._service_registry,
                states=("installed",),
                exclude_addons=[current_addon],
            )
            RestServiceRegistration._build_controllers_routes(
                class_or_instance._service_registry
            )

        # register our base component
        BaseRestService._build_component(class_or_instance.comp_registry)

        # Define a base test controller here to avoid to have this controller
        # registered outside tests
        class_or_instance._collection_name = "base.rest.test"

        class BaseTestController(RestController):
            _root_path = "/test_controller/"
            _collection_name = class_or_instance._collection_name
            _default_auth = "public"

        class_or_instance._BaseTestController = BaseTestController

    @staticmethod
    def _teardown_registry(class_or_instance):
        ComponentRegistryCase._teardown_registry(class_or_instance)
        http.controllers_per_module = class_or_instance._controllers_per_module
        db_name = get_db_name()
        _component_databases[db_name] = class_or_instance._original_components
        _rest_services_databases[
            db_name
        ] = class_or_instance._original_services_registry

    def _build_services(self, *classes):
        self._build_components(*classes)
        with new_rollbacked_env() as env:
            RestServiceRegistration = env["rest.service.registration"]
            current_addon = _get_addon_name(self.__module__)
            RestServiceRegistration.load_services(current_addon, self._service_registry)
            RestServiceRegistration._build_controllers_routes(self._service_registry)

    def _get_controller_for(self, service):
        addon_name = "{}_{}_{}".format(
            get_db_name(),
            service._collection.replace(".", "_"),
            service._usage.replace(".", "_"),
        )
        controllers = http.controllers_per_module.get(addon_name, [])
        if not controllers:
            return
        return controllers[0][1]

    def _get_controller_route_methods(self, controller):
        methods = {}
        for name, method in _inspect_methods(controller):
            if hasattr(method, "routing"):
                methods[name] = method
        return methods


class TransactionRestServiceRegistryCase(TransactionCase, RestServiceRegistryCase):

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not use
        # super)
        TransactionCase.setUp(self)
        RestServiceRegistryCase._setup_registry(self)

    def tearDown(self):
        RestServiceRegistryCase._teardown_registry(self)
        TransactionCase.tearDown(self)

    def _get_service_component(self, usage):
        collection = _PseudoCollection(self._collection_name, self.env)
        work = WorkContext(
            model_name="rest.service.registration",
            collection=collection,
            components_registry=self.comp_registry,
        )
        return work.component(usage=usage)


class BaseRestCase(SavepointComponentCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.registry.enter_test_mode(self.env.cr)
        self.base_url = self.env["ir.config_parameter"].get_param("web.base.url")

    def tearDown(self):
        self.registry.leave_test_mode()
        super().tearDown()
