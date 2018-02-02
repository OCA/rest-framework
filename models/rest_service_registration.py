# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
"""

REST Service Registy Builder
============================

Resister available REST service at the build of a registry.

This code is inspired by ``odoo.addons.component.builder.ComponentBuilder``

"""

from odoo import api, models
from ..core import (
    _rest_services_databases,
    _rest_controllers_per_module,
    RestServicesRegistry
)


class RestServiceRegistation(models.AbstractModel):
    """Register REST services into the REST services registry

    This class allows us to hook the registration of the collection and the
    root url of all the REST services installed into the current database at
    the end of the Odoo's registry loading, using ``_register_hook``. This
    method is called after all modules are loaded, so we are sure that we only
    register REST services installed into the current database.


    To register a controller providing REST service, you must inherit from
    this current model and implement the method ``_get_registry_items``
    This method must return a list a list of tuple (root_path, collection_name)
    The root_path is the root of the path on which the methods of your
    `` RestController`` are registred.
    The collection_name is the name of the collection on which your
    ``RestServiceComponent`` implementing the business logic of your service
    is registered.


     ::
         # The implemented service will be available at '/my_rest_api/ping'

         from odoo.addons.component.core import Component

         class PingService(Component):
             _inherit = 'base.rest.service'
             _name = 'ping.service'
             _usage = 'ping'
             _collection = 'my.collection'

             def get(self, _id, message):
                 return {
                     'response': 'GET with message ' + message}

             # Validator
             def _validator_get(self):
                 return {'message': {'type': 'string'}}


         from odoo.addons.base_rest.controllers import main

         ROOT_PATH = '/my_rest_api/'

         class RestController(main.RestController):

             @route([
                 ROOT_PATH + '<string:_service_name>',
                 ROOT_PATH + '<string:_service_name>/search',
                 ROOT_PATH + '<string:_service_name>/<int:_id>',
                 ROOT_PATH + '<string:_service_name>/<int:_id>/get'
             ], methods=['GET'], auth="api_key", csrf=False)
             def get(self, _service_name, _id=None, **params):
                 method_name = 'get' if _id else 'search'
                 return self._process_method(
                     _service_name, method_name, _id, params)

         from odoo import models

         class RestServiceRegistation(models.AbstractModel):
             _inherit = 'rest.service.registration'

             def _get_registry_items(self):
                 res = super(
                     RestServiceRegistation, self)._get_registry_items()
                 res.append((ROOT_PATH, 'my.collection')

    """

    _name = 'rest.service.registration'
    _description = 'REST Services Registration Model'

    @api.model_cr
    def _register_hook(self):
        # This method is called by Odoo when the registry is built,
        # so in case the registry is rebuilt (cache invalidation, ...),
        # we have to to rebuild the registry. We use a new
        # registry so we have an empty cache and we'll add services in it.
        services_registry = self._init_global_registry()
        query = (
            "SELECT name "
            "FROM ir_module_module "
            "WHERE state IN %s "
        )
        self.env.cr.execute(query, (('installed', 'to upgrade'), ))
        module_list = [name for (name,) in self.env.cr.fetchall()]
        for module in module_list:
            controller_defs = _rest_controllers_per_module.get(module, [])
            for controller_def in controller_defs:
                services_registry[controller_def['root_path']] = controller_def

    def _init_global_registry(self):
        services_registry = RestServicesRegistry()
        _rest_services_databases[self.env.cr.dbname] = services_registry
        return services_registry

    def _get_registry_items(self):
        return []
