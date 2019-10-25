# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""

REST Service Registy Builder
============================

Register available REST services at the build of a registry.

This code is inspired by ``odoo.addons.component.builder.ComponentBuilder``

"""
import odoo
from odoo import http, models

from ..core import (
    RestServicesRegistry,
    _rest_controllers_per_module,
    _rest_services_databases,
)


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
