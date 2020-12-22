To add your own REST service you must provides at least 2 classes.

* A Component providing the business logic of your service,
* A Controller to register your service.

The business logic of your service must be implemented into a component
(``odoo.addons.component.core.Component``) that inherit from
'base.rest.service'

Initially, base_rest expose by default all public methods defined in a service.
The conventions for accessing methods via HTTP were as follows:

* The method ``def get(self, _id)`` if defined, is accessible via HTTP GET routes ``<string:_service_name>/<int:_id>`` and ``<string:_service_name>/<int:_id>/get``.
* The method ``def search(self, **params)`` if defined, is accessible via the HTTP GET routes ``<string:_service_name>/`` and ``<string:_service_name>/search``.
* The method ``def delete(self, _id)`` if defined, is accessible via the HTTP DELETE route ``<string:_service_name>/<int:_id>``.
* The ``def update(self, _id, **params)`` method, if defined, is accessible via the HTTP PUT route ``<string:_service_name>/<int:_id>``.
* Other methods are only accessible via HTTP POST routes ``<string:_service_name>`` or ``<string:_service_name>/<string:method_name>`` or ``<string:_service_name>/<int:_id>`` or ``<string:_service_name>/<int:_id>/<string:method_name>``

.. code-block:: python

    from odoo.addons.component.core import Component


    class PingService(Component):
        _inherit = 'base.rest.service'
        _name = 'ping.service'
        _usage = 'ping'
        _collection = 'my_module.services'


        # The following method are 'public' and can be called from the controller.
        def get(self, _id, message):
            return {
                'response': 'Get called with message ' + message}

        def search(self, message):
            return {
                'response': 'Search called search with message ' + message}

        def update(self, _id, message):
            return {'response': 'PUT called with message ' + message}

        # pylint:disable=method-required-super
        def create(self, **params):
            return {'response': 'POST called with message ' + params['message']}

        def delete(self, _id):
            return {'response': 'DELETE called with id %s ' % _id}

        # Validator
        def _validator_search(self):
            return {'message': {'type': 'string'}}

        # Validator
        def _validator_get(self):
            # no parameters by default
            return {}

        def _validator_update(self):
            return {'message': {'type': 'string'}}

        def _validator_create(self):
            return {'message': {'type': 'string'}}

Once you have implemented your services (ping, ...), you must tell to Odoo
how to access to these services. This process is done by implementing a
controller that inherits from  ``odoo.addons.base_rest.controllers.main.RestController``

.. code-block:: python

    from odoo.addons.base_rest.controllers import main

    class MyRestController(main.RestController):
        _root_path = '/my_services_api/'
        _collection_name = my_module.services

In your controller, _'root_path' is used to specify the root of the path to
access to your services and '_collection_name' is the name of the collection
providing the business logic for the requested service/


By inheriting from ``RestController`` the following routes will be registered
to access to your services

.. code-block:: python

    @route([
        ROOT_PATH + '<string:_service_name>',
        ROOT_PATH + '<string:_service_name>/search',
        ROOT_PATH + '<string:_service_name>/<int:_id>',
        ROOT_PATH + '<string:_service_name>/<int:_id>/get'
    ], methods=['GET'], auth="user", csrf=False)
    def get(self, _service_name, _id=None, **params):
        method_name = 'get' if _id else 'search'
        return self._process_method(_service_name, method_name, _id, params)

    @route([
        ROOT_PATH + '<string:_service_name>',
        ROOT_PATH + '<string:_service_name>/<string:method_name>',
        ROOT_PATH + '<string:_service_name>/<int:_id>',
        ROOT_PATH + '<string:_service_name>/<int:_id>/<string:method_name>'
    ], methods=['POST'], auth="user", csrf=False)
    def modify(self, _service_name, _id=None, method_name=None, **params):
        if not method_name:
            method_name = 'update' if _id else 'create'
        if method_name == 'get':
            _logger.error("HTTP POST with method name 'get' is not allowed. "
                          "(service name: %s)", _service_name)
            raise BadRequest()
        return self._process_method(_service_name, method_name, _id, params)

    @route([
        ROOT_PATH + '<string:_service_name>/<int:_id>',
    ], methods=['PUT'], auth="user", csrf=False)
    def update(self, _service_name, _id, **params):
        return self._process_method(_service_name, 'update', _id, params)

    @route([
        ROOT_PATH + '<string:_service_name>/<int:_id>',
    ], methods=['DELETE'], auth="user", csrf=False)
    def delete(self, _service_name, _id):
        return self._process_method(_service_name, 'delete', _id)


As result an HTTP GET call to 'http://my_odoo/my_services_api/ping' will be
dispatched to the method ``PingService.search``

In addition to easily exposing your methods, the module allows you to define
data schemas to which the exchanged data must conform. These schemas are defined
on the basis of `Cerberus schemas <https://docs.python-cerberus.org/en/stable/>`_
and associated to the methods using the
following naming convention. For a method `my_method`:

* ``def _validator_my_method(self):`` will be called to get the schema required to
  validate the input parameters.
* ``def _validator_return_my_method(self):`` if defined, will be called to get
  the schema used to validate the response.

In order to offer even more flexibility, a new API has been developed.

This new API replaces the implicit approach used to expose a service by the use
of a python decorator to explicitly mark a method as being available via the
REST API: ``odoo.addons.base_rest.restapi.method``.


.. code-block:: python

    class PartnerNewApiService(Component):
        _inherit = "base.rest.service"
        _name = "partner.new_api.service"
        _usage = "partner"
        _collection = "base.rest.demo.new_api.services"
        _description = """
            Partner New API Services
            Services developed with the new api provided by base_rest
        """

        @restapi.method(
            [(["/<int:id>/get", "/<int:id>"], "GET")],
            output_param=restapi.CerberusValidator("_get_partner_schema"),
            auth="public",
        )
        def get(self, _id):
            return {"name": self.env["res.partner"].browse(_id).name}

        def _get_partner_schema(self):
            return {
                "name": {"type": "string", "required": True}
            }

Thanks to this new api, you are now free to specify your own routes but also
to use other object types as parameter or response to your methods.
For example, `base_rest_datamodel` allows you to use Datamodel object instance
into your services.

.. code-block:: python

    from marshmallow import fields

    from odoo.addons.base_rest import restapi
    from odoo.addons.component.core import Component
    from odoo.addons.datamodel.core import Datamodel


    class PartnerSearchParam(Datamodel):
        _name = "partner.search.param"

        id = fields.Integer(required=False, allow_none=False)
        name = fields.String(required=False, allow_none=False)


    class PartnerShortInfo(Datamodel):
        _name = "partner.short.info"

        id = fields.Integer(required=True, allow_none=False)
        name = fields.String(required=True, allow_none=False)


    class PartnerNewApiService(Component):
        _inherit = "base.rest.service"
        _name = "partner.new_api.service"
        _usage = "partner"
        _collection = "base.rest.demo.new_api.services"
        _description = """
            Partner New API Services
            Services developed with the new api provided by base_rest
        """

        @restapi.method(
            [(["/", "/search"], "GET")],
            input_param=restapi.Datamodel("partner.search.param"),
            output_param=restapi.Datamodel("partner.short.info", is_list=True),
            auth="public",
        )
        def search(self, partner_search_param):
            """
            Search for partners
            :param partner_search_param: An instance of partner.search.param
            :return: List of partner.short.info
            """
            domain = []
            if partner_search_param.name:
                domain.append(("name", "like", partner_search_param.name))
            if partner_search_param.id:
                domain.append(("id", "=", partner_search_param.id))
            res = []
            PartnerShortInfo = self.env.datamodels["partner.short.info"]
            for p in self.env["res.partner"].search(domain):
                res.append(PartnerShortInfo(id=p.id, name=p.name))
            return res
