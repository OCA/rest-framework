# Copyright 2017 Akretion (http://www.akretion.com).
# Copyright 2020 ACSONE SA/NV
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Laurent Mignon <laurent.mignon@acsone.eu>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import copy

from odoo import http
from odoo.tests.common import SavepointCase, TransactionCase, get_db_name

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

from ..controllers.main import RestController, _PseudoCollection
from ..core import (
    RestServicesRegistry,
    _rest_controllers_per_module,
    _rest_services_databases,
)
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
        class_or_instance._original_addon_rest_controllers_per_module = copy.deepcopy(
            _rest_controllers_per_module[_get_addon_name(class_or_instance.__module__)]
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

        # register our components
        class_or_instance.comp_registry.load_components("base_rest")

        # Define a base test controller here to avoid to have this controller
        # registered outside tests
        class_or_instance._collection_name = "base.rest.test"

        BaseTestController = class_or_instance._get_test_controller(class_or_instance)

        class_or_instance._BaseTestController = BaseTestController
        class_or_instance._controller_route_method_names = {
            "my_controller_route_without",
            "my_controller_route_with",
            "my_controller_route_without_auth_2",
        }

    @staticmethod
    def _get_test_controller(class_or_instance, root_path="/test_controller/"):
        class BaseTestController(RestController):
            _root_path = root_path
            _collection_name = class_or_instance._collection_name
            _default_auth = "public"

            @http.route("/my_controller_route_without")
            def my_controller_route_without(self):
                return {}

            @http.route(
                "/my_controller_route_with",
                auth="public",
                cors="http://with_cors",
                csrf="False",
                save_session="False",
            )
            def my_controller_route_with(self):
                return {}

            @http.route("/my_controller_route_without_auth_2", auth=None)
            def my_controller_route_without_auth_2(self):
                return {}

        return BaseTestController

    @staticmethod
    def _teardown_registry(class_or_instance):
        ComponentRegistryCase._teardown_registry(class_or_instance)
        http.controllers_per_module = class_or_instance._controllers_per_module
        db_name = get_db_name()
        _component_databases[db_name] = class_or_instance._original_components
        _rest_services_databases[
            db_name
        ] = class_or_instance._original_services_registry
        class_or_instance._service_registry = {}
        _rest_controllers_per_module[
            _get_addon_name(class_or_instance.__module__)
        ] = class_or_instance._original_addon_rest_controllers_per_module

    @staticmethod
    def _build_services(class_or_instance, *classes):
        class_or_instance._build_components(*classes)
        with new_rollbacked_env() as env:
            RestServiceRegistration = env["rest.service.registration"]
            current_addon = _get_addon_name(class_or_instance.__module__)
            RestServiceRegistration.load_services(
                current_addon, class_or_instance._service_registry
            )
            RestServiceRegistration._build_controllers_routes(
                class_or_instance._service_registry
            )

    @staticmethod
    def _get_controller_for(service):
        addon_name = "{}_{}_{}".format(
            get_db_name(),
            service._collection.replace(".", "_"),
            service._usage.replace(".", "_"),
        )
        controllers = http.controllers_per_module.get(addon_name, [])
        if not controllers:
            return
        return controllers[0][1]

    @staticmethod
    def _get_controller_route_methods(controller):
        methods = {}
        for name, method in _inspect_methods(controller):
            if hasattr(method, "routing"):
                methods[name] = method
        return methods

    @staticmethod
    def _get_service_component(class_or_instance, usage):
        collection = _PseudoCollection(
            class_or_instance._collection_name, class_or_instance.env
        )
        work = WorkContext(
            model_name="rest.service.registration",
            collection=collection,
            components_registry=class_or_instance.comp_registry,
        )
        return work.component(usage=usage)


class TransactionRestServiceRegistryCase(TransactionCase, RestServiceRegistryCase):

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not use
        # super)
        TransactionCase.setUp(self)
        RestServiceRegistryCase._setup_registry(self)
        self.base_url = self.env["ir.config_parameter"].get_param("web.base.url")

    def tearDown(self):
        RestServiceRegistryCase._teardown_registry(self)
        TransactionCase.tearDown(self)


class SavepointRestServiceRegistryCase(SavepointCase, RestServiceRegistryCase):

    # pylint: disable=W8106
    @classmethod
    def setUpClass(cls):
        # resolve an inheritance issue (common.SavepointCase does not use
        # super)
        SavepointCase.setUpClass()
        RestServiceRegistryCase._setup_registry(cls)
        cls.base_url = cls.env["ir.config_parameter"].get_param("web.base.url")

    @classmethod
    def tearDownClass(cls):
        RestServiceRegistryCase._teardown_registry(cls)
        SavepointCase.tearDownClass()


class BaseRestCase(SavepointComponentCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()
        cls.base_url = cls.env["ir.config_parameter"].get_param("web.base.url")

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)
        self.registry.enter_test_mode(self.env.cr)

    def tearDown(self):
        self.registry.leave_test_mode()
        super().tearDown()
