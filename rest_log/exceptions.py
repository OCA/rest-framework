# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>

from odoo import exceptions as odoo_exceptions, http as odoo_http


class RESTServiceDispatchException(Exception):

    rest_json_info = {}

    def __init__(self, message, log_entry_url=None, **kw):
        super().__init__(message)
        self.rest_json_info = dict(log_entry_url=log_entry_url, **kw)


class RESTServiceUserErrorException(
    RESTServiceDispatchException, odoo_exceptions.UserError
):
    """User error wrapped exception."""


class RESTServiceValidationErrorException(
    RESTServiceDispatchException, odoo_exceptions.ValidationError
):
    """Validation error wrapped exception."""


class RESTServiceMissingErrorException(
    RESTServiceDispatchException, odoo_exceptions.MissingError
):
    """Missing error wrapped exception."""


class RESTServiceSessionExpiredException(
    RESTServiceDispatchException, odoo_http.SessionExpiredException
):
    """Session expired wrapped exception."""


class RESTServiceAccessDeniedException(
    RESTServiceDispatchException, odoo_exceptions.AccessDenied
):
    """Access denied wrapped exception."""


class RESTServiceAuthenticationErrorException(
    RESTServiceDispatchException, odoo_http.AuthenticationError
):
    """Authentication error wrapped exception."""


class RESTServiceAccessErrorException(
    RESTServiceDispatchException, odoo_exceptions.AccessError
):
    """Access error wrapped exception."""


EXCEPTION_MAP = {
    odoo_exceptions.AccessDenied: RESTServiceAccessDeniedException,
    odoo_exceptions.AccessError: RESTServiceAccessErrorException,
    odoo_exceptions.MissingError: RESTServiceMissingErrorException,
    odoo_exceptions.UserError: RESTServiceUserErrorException,
    odoo_exceptions.ValidationError: RESTServiceValidationErrorException,
    odoo_http.AuthenticationError: RESTServiceAuthenticationErrorException,
    odoo_http.SessionExpiredException: RESTServiceSessionExpiredException,
}
