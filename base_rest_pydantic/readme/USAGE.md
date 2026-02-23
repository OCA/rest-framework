To use Pydantic instances as request and/or response of a REST service
endpoint you must:

- Define your Pydantic classes;
- Provides the information required to the
  `odoo.addons.base_rest.restapi.method` decorator;

``` python
from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.pydantic.models import BaseModel

class PingMessage(BaseModel):
    message: str


class PingService(Component):
    _inherit = 'base.rest.service'
    _name = 'ping.service'
    _usage = 'ping'
    _collection = 'my_module.services'


    @restapi.method(
        [(["/pong"], "GET")],
        input_param=restapi.PydanticModel(PingMessage),
        output_param=restapi.PydanticModel(PingMessage),
        auth="public",
    )
    def pong(self, ping_message):
        return PingMessage(message = "Received: " + ping_message.message)
```
