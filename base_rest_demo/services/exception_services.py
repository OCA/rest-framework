# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from werkzeug.exceptions import MethodNotAllowed

from odoo import _
from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import SessionExpiredException

from odoo.addons.component.core import Component


class ExceptionService(Component):
    _inherit = "base.rest.service"
    _name = "exception.service"
    _usage = "exception"
    _collection = "base.rest.demo.public.services"
    _description = """
        Exception Services

        Services to test hiw exception are handled by base_erst
    """

    def user_error(self):
        """
        Simulate an odoo.exceptions.UserError
        Should be translated into BadRequest with a description into the json
        body
        """
        raise UserError(_("UserError message"))

    def validation_error(self):
        """
        Simulate an odoo.exceptions.ValidationError
        Should be translated into BadRequest with a description into the json
        body
        """
        raise ValidationError(_("ValidationError message"))

    def session_expired(self):
        """
        Simulate an odoo.http.SessionExpiredException
        Should be translated into Unauthorized without description into the
        json body
        """
        raise SessionExpiredException("Expired message")

    def missing_error(self):
        """
        Simulate an odoo.exceptions.MissingError
        Should be translated into NotFound without description into the json
        body
        """
        raise MissingError(_("Missing message"))

    def access_error(self):
        """
        Simulate an odoo.exceptions.AccessError
        Should be translated into Forbidden without description into the json
        body
        """
        raise AccessError(_("Access error message"))

    def access_denied(self):
        """
        Simulate an odoo.exceptions.AccessDenied
        Should be translated into Forbidden without description into the json
        body
        """
        raise AccessDenied()

    def http_exception(self):
        """
        Simulate an werkzeug.exceptions.MethodNotAllowed
        This exception is not by the framework
        """
        raise MethodNotAllowed(description="Method not allowed message")

    def bare_exception(self):
        """
        Simulate a python exception.
        Should be translated into InternalServerError without description into
        the json body
        """
        raise IOError("My IO error")

    # Validator
    def _validator_user_error(self):
        return {}

    def _validator_return_user_error(self):
        return {}

    def _validator_validation_error(self):
        return {}

    def _validator_return_validation_error(self):
        return {}

    def _validator_session_expired(self):
        return {}

    def _validator_return_session_expired(self):
        return {}

    def _validator_missing_error(self):
        return {}

    def _validator_return_missing_error(self):
        return {}

    def _validator_access_error(self):
        return {}

    def _validator_return_access_error(self):
        return {}

    def _validator_access_denied(self):
        return {}

    def _validator_return_access_denied(self):
        return {}

    def _validator_http_exception(self):
        return {}

    def _validator_return_http_exception(self):
        return {}

    def _validator_bare_exception(self):
        return {}

    def _validator_return_bare_exception(self):
        return {}
