# Copyright 2017 Camptocamp SA
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

"""

Datamodels Builder
==================

Build the datamodels at the build of a registry.

"""
from odoo import models, modules

from .core import DEFAULT_CACHE_SIZE, DatamodelRegistry, _datamodel_databases


class DatamodelBuilder(models.AbstractModel):
    """Build the datamodel classes

    And register them in a global registry.

    Every time an Odoo registry is built, the know datamodels are cleared and
    rebuilt as well.  The Datamodel classes are built using the same mechanism
    than Odoo's Models: a final class is created, taking every Datamodels with
    a ``_name`` and applying Datamodels with an ``_inherits`` upon them.

    The final Datamodel classes are registered in global registry.

    This class is an Odoo model, allowing us to hook the build of the
    datamodels at the end of the Odoo's registry loading, using
    ``_register_hook``. This method is called after all modules are loaded, so
    we are sure that we have all the datamodels Classes and in the correct
    order.

    """

    _name = "datamodel.builder"
    _description = "Datamodel Builder"

    _datamodels_registry_cache_size = DEFAULT_CACHE_SIZE

    def _register_hook(self):
        # This method is called by Odoo when the registry is built,
        # so in case the registry is rebuilt (cache invalidation, ...),
        # we have to rebuild the datamodels. We use a new
        # registry so we have an empty cache and we'll add datamodels in it.
        datamodels_registry = self._init_global_registry()
        self.build_registry(datamodels_registry)
        datamodels_registry.ready = True

    def _init_global_registry(self):
        datamodels_registry = DatamodelRegistry(
            cachesize=self._datamodels_registry_cache_size
        )
        _datamodel_databases[self.env.cr.dbname] = datamodels_registry
        return datamodels_registry

    def build_registry(self, datamodels_registry, states=None, exclude_addons=None):
        if not states:
            states = ("installed", "to upgrade")
        # lookup all the installed (or about to be) addons and generate
        # the graph, so we can load the datamodels following the order
        # of the addons' dependencies
        graph = modules.graph.Graph()
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
            self.load_datamodels(module.name, datamodels_registry=datamodels_registry)

    def load_datamodels(self, module, datamodels_registry=None):
        """Build every datamodel known by MetaDatamodel for an odoo module

        The final datamodel (composed by all the Datamodel classes in this
        module) will be pushed into the registry.

        :param module: the name of the addon for which we want to load
                       the datamodels
        :type module: str | unicode
        :param registry: the registry in which we want to put the Datamodel
        :type registry: :py:class:`~.core.DatamodelRegistry`
        """
        datamodels_registry = (
            datamodels_registry or _datamodel_databases[self.env.cr.dbname]
        )
        datamodels_registry.load_datamodels(module)
