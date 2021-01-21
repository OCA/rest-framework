# Copyright 2021 Camptocamp
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.addons.component.core import Component


class BaseRestCerberusValidator(Component):
    """Component used to lookup the input/output validator methods

    To modify in your services collection::

        class MyCollectionRestCerberusValidator(Component):
            _name = "mycollection.rest.cerberus.validator"
            _inherit = "base.rest.cerberus.validator"
            _usage = "cerberus.validator"
            _collection = "mycollection"

            def get_validator_handler(self, service, method_name, direction):
                # customize

            def has_validator_handler(self, service, method_name, direction):
                # customize

    """

    _name = "base.rest.cerberus.validator"
    _usage = "cerberus.validator"
    _is_rest_service_component = False  # marker to retrieve REST components

    def get_validator_handler(self, service, method_name, direction):
        """Get the validator handler for a method

        By default, it returns the method on the current service instance. It
        can be customized to delegate the validators to another component.

        The returned method will be called without arguments, and is expected
        to return the schema.

        direction is either "input" for request schema or "output" for responses.
        """
        return getattr(service, method_name)

    def has_validator_handler(self, service, method_name, direction):
        """Return if the service has a validator handler for a method

        By default, it returns True if the the method exists on the service. It
        can be customized to delegate the validators to another component.

        The returned method will be called without arguments, and is expected
        to return the schema.

        direction is either "input" for request schema or "output" for responses.
        """
        return hasattr(service, method_name)
