To add your own REST service you must provides at least 2 classes.

* A Component providing the business logic of your service,
* A Controller to register your service.

The business logic of your service must be implemented into a component
(``odoo.addons.component.core.Component``) that inherit from
'base.rest.service'

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

Once your have implemented your services (ping, ...), you must tell to Odoo
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


The HTTP GET 'http://my_odoo/my_services_api/ping' will be dispatched to the
method ``PingService.search``