# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>

from odoo import exceptions as odoo_exceptions


class RESTServiceDispatchException(Exception):

    rest_json_info = {}

    def __init__(self, message, log_entry_url):
        super().__init__(message)
        self.rest_json_info = {"log_entry_url": log_entry_url}


class RESTServiceUserErrorException(
    RESTServiceDispatchException, odoo_exceptions.UserError
):
    """User error wrapped exception."""


class RESTServiceValidationErrorException(
    RESTServiceDispatchException, odoo_exceptions.ValidationError
):
    """Validation error wrapped exception."""
