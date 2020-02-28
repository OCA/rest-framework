# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class PingService(Component):
    _inherit = "base.rest.service"
    _name = "ping.service"
    _usage = "ping"
    _collection = "base.rest.demo.public.services"
    _description = """
        Ping Services
        Access to the ping services is allowed to everyone
    """

    # The following method are 'public' and can be called from the controller.
    def get(self, _id, message):
        """
        This method is used to get the information of the object specified
        by Id.
        """
        return {"message": message, "id": _id}

    def search(self, **params):
        """
        A search method to illustrate how you can define a complex request.
        In the case of the methods 'get' and 'search' the parameters are
        passed to the server as the query part of the service URL.
        """
        return {"response": "Search called search with params %s" % params}

    def update(self, _id, message):
        """
        Update method description ...
        """
        return {"response": "PUT called with message " + message}

    # pylint:disable=method-required-super
    def create(self, **params):
        """
        Create method description ...
        """
        return {"response": "POST called with message " + params["message"]}

    def delete(self, _id):
        """
        Delete method description ...
        """
        return {"response": "DELETE called with id %s " % _id}

    # Validator
    def _validator_search(self):
        return {
            "param_string": {"type": "string"},
            "param_required": {"type": "string", "required": True},
            "limit": {"type": "integer", "default": 50, "coerce": to_int},
            "offset": {"type": "integer", "default": 0, "coerce": to_int},
            "params": {"type": "list", "schema": {"type": "string"}},
        }

    def _validator_return_search(self):
        return {"response": {"type": "string"}}

    # Validator
    def _validator_get(self):
        return {"message": {"type": "string"}}

    def _validator_return_get(self):
        return {"message": {"type": "string"}, "id": {"type": "integer"}}

    def _validator_update(self):
        return {"message": {"type": "string"}}

    def _validator_return_update(self):
        return {"response": {"type": "string"}}

    def _validator_create(self):
        return {"message": {"type": "string"}}

    def _validator_return_create(self):
        return {"response": {"type": "string"}}

    def _validator_return_delete(self):
        return {"response": {"type": "string"}}
