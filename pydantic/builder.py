# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

"""

Pydantic Models Builder
=======================

Build the pydantic models at the build of a registry by resolving the
inheritance declaration and ForwardRefs type declaration into the models

"""
from typing import List, Optional

import odoo
from odoo import api, models as omodels

from .registry import PydanticClassesRegistry, _pydantic_classes_databases


class PydanticClassesBuilder(omodels.AbstractModel):
    """Build the component classes

    And register them in a global registry.

    Every time an Odoo registry is built, the know pydantic models are cleared and
    rebuilt as well.  The pydantic classes are built by taking every models with
    a ``__xreg_name__`` and applying pydantic models with an ``__xreg_base_names__``
    upon them.

    The final pydantic classes are registered in global registry.

    This class is an Odoo model, allowing us to hook the build of the
    pydantic classes at the end of the Odoo's registry loading, using
    ``_register_hook``. This method is called after all modules are loaded, so
    we are sure that we have all the components Classes and in the correct
    order.

    """

    _name = "pydantic.classes.builder"
    _description = "Pydantic Classes Builder"

    def _register_hook(self):
        # This method is called by Odoo when the registry is built,
        # so in case the registry is rebuilt (cache invalidation, ...),
        # we have to to rebuild the components. We use a new
        # registry so we have an empty cache and we'll add components in it.
        registry = self._init_global_registry()
        self.build_registry(registry)

    @api.model
    def _init_global_registry(self):
        registry = PydanticClassesRegistry()
        _pydantic_classes_databases[self.env.cr.dbname] = registry
        return registry

    @api.model
    def build_registry(
        self,
        registry: PydanticClassesRegistry,
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

        registry.init_registry([m.name for m in graph])
