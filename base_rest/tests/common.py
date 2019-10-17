# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import _get_addon_name
from odoo.addons.component.tests.common import (
    SavepointComponentCase,
    new_rollbacked_env,
)


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
            env["rest.service.registration"].load_services(
                current_addon, services_registry
            )


class BaseRestCase(SavepointComponentCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super(BaseRestCase, cls).setUpClass()
        cls.setUpRegistry()

    def setUp(self, *args, **kwargs):
        super(BaseRestCase, self).setUp(*args, **kwargs)

        self.registry.enter_test_mode(self.env.cr)
        self.base_url = self.env["ir.config_parameter"].get_param("web.base.url")

    def tearDown(self):
        self.registry.leave_test_mode()
        super(BaseRestCase, self).tearDown()
