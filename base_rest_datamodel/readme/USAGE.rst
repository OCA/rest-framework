To use DataModel instances as request and/or response of a REST service endpoint
you must:

* Define your DataModel objects;
* Provides the information required to the ``odoo.addons.base_rest.restapi.method`` decorator;


.. code-block:: python

    from marshmallow import fields

    from odoo.addons.base_rest import restapi
    from odoo.addons.component.core import Component
    from odoo.addons.datamodel.core import Datamodel

    class PingMessage(Datamodel):
        _name = "ping.message"

        message = fields.String(required=True, allow_none=False)


    class PingService(Component):
        _inherit = 'base.rest.service'
        _name = 'ping.service'
        _usage = 'ping'
        _collection = 'my_module.services'


        @restapi.method(
            [(["/pong"], "GET")],
            input_param=restapi.Datamodel("ping.message"),
            output_param=restapi.Datamodel("ping.message"),
            auth="public",
        )
        def pong(self, ping_message):
            PingMessage = self.env.datamodels["ping.message"]
            return PingMessage(message = "Received: " + ping_message.message)
