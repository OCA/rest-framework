# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""

Extendale classes Loader
========================

Load the extendable classes at the build of a registry.

"""
from typing import List, Optional

import odoo
from odoo import api, models

from extendable.registry import ExtendableClassesRegistry

from ..registry import _extendable_registries_database


class ExtendableRegistryLoader(models.AbstractModel):
    _name = "extendable.registry.loader"
    _description = "Extendable Registry Loader"

    def _register_hook(self):
        # This method is called by Odoo when the registry is built,
        # so in case the registry is rebuilt (cache invalidation, ...),
        # we have to to rebuild the extendable classes. We use a new
        # registry so we have an empty cache and we'll add extendable classes
        # in it.
        registry = self._init_global_registry()
        self.build_registry(registry)

    @api.model
    def _init_global_registry(self):
        registry = ExtendableClassesRegistry()
        _extendable_registries_database[self.env.cr.dbname] = registry
        return registry

    @api.model
    def build_registry(
        self,
        registry: ExtendableClassesRegistry,
        states: Optional[List[str]] = None,
        exclude_addons: Optional[List[str]] = None,
    ):
        if not states:
            states = ("installed", "to upgrade")
        # lookup all the installed (or about to be) addons and generate
        # the graph, so we can load the components following the order
        # of the addons' dependencies
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
        module_matchings = []
        for m in graph:
            module_matchings.append(f"odoo.addons.{m.name}.*")
        registry.init_registry(module_matchings)
