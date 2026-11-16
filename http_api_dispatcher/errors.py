# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Map exceptions to JSON responses.

Heavily inspired by `wrapJsonException` and `RestApiDispatcher.handle_error`
in `base_rest.http` (OCA/rest-framework): same mapping of exceptions,
same body format.

The format of the body is compatible with `base_rest`:

    {"code": 400, "name": "Bad Request", "description": "..."}

plus any key provided by the `rest_json_info` attribute of the exception.
"""

import logging
import traceback

from markupsafe import escape
from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    Unauthorized,
)

from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import Response, SessionExpiredException
from odoo.tools import str2bool
from odoo.tools.config import config

from .encoder import json_dumps

_logger = logging.getLogger(__name__)

BLACKLISTED_LOG_PARAMS = ("password",)
BLACKLISTED_LOG_HEADERS = ("Api-Key", "Authorization", "Cookie")
# Request data is untrusted: never log more than this per value
LOG_MAX_VALUE_LENGTH = 500


class ApiValidationError(UserError):
    """Raised when request params are not valid.

    The detail of the errors is returned in the `errors` key of the body.
    """

    def __init__(self, message, errors=None):
        """Keep the details of the errors to return them to the client."""
        super().__init__(message)
        self.rest_json_info = {"errors": errors} if errors else {}


# (exception classes, HTTP exception class, include description)
# Order matters: MissingError and AccessError are UserError subclasses.
DEFAULT_ERROR_MAP = (
    (SessionExpiredException, Unauthorized, False),
    (MissingError, NotFound, False),
    ((AccessError, AccessDenied), Forbidden, False),
    ((UserError, ValidationError), BadRequest, True),
)


def _config_flag(section, key):
    """Read a boolean from the configuration file.

    Values coming from the file are strings: "False" must be falsy.
    """
    value = config.get_misc(section, key)
    if isinstance(value, str):
        return str2bool(value, default=False)
    return bool(value)


def is_dev_mode():
    """Return True if errors must include their traceback."""
    return (
        _config_flag("http_api", "dev_mode")
        # Backward compatibility w/ base_rest configuration
        or _config_flag("base_rest", "dev_mode")
    )


class ErrorMapper:
    """Turn any exception into a JSON response.

    The map can be extended per route via the `error_map` routing key:
    its entries have the same format of `DEFAULT_ERROR_MAP`
    and are evaluated first.
    """

    def __init__(self, error_map=None, request=None, encoder=None):
        """Prepend route specific mappings to the default ones."""
        self.error_map = tuple(error_map or ()) + DEFAULT_ERROR_MAP
        self.request = request
        self.encoder = encoder

    @classmethod
    def for_routing(cls, routing, request=None):
        """Build a mapper from the routing keys of a route."""
        routing = routing or {}
        return cls(
            error_map=routing.get("error_map"),
            request=request,
            encoder=routing.get("json_encoder"),
        )

    def to_response(self, exc):
        """Return the response for given exception, logging it."""
        if isinstance(exc, HTTPException) and (
            exc.response is not None or (exc.code or 0) < 400
        ):
            # Explicit response (eg: `werkzeug.exceptions.abort(response)`)
            # or not an error (eg: redirections).
            return exc
        http_exc, include_description = self._map(exc)
        body = self._get_body(exc, http_exc, include_description)
        self._log(exc, http_exc, body)
        response = Response(
            json_dumps(body, encoder=self.encoder),
            status=http_exc.code,
            content_type="application/json",
        )
        for key, value in http_exc.get_headers():
            if key.lower() != "content-type":
                response.headers[key] = value
        return response

    def _map(self, exc):
        """Return the HTTP exception to use and whether to show the description."""
        for exc_classes, http_exc_class, include_description in self.error_map:
            if isinstance(exc, exc_classes):
                return http_exc_class(self._message(exc)), include_description
        if isinstance(exc, HTTPException):
            # Client errors raised explicitly carry a meaningful description
            return exc, exc.code < 500
        return InternalServerError(), False

    def _message(self, exc):
        """Message of the exception, used as description."""
        return exc.args[0] if exc.args else str(exc)

    def _get_body(self, exc, http_exc, include_description):
        """Build the JSON body in the format of `base_rest`."""
        body = {"code": http_exc.code, "name": str(escape(http_exc.name))}
        if include_description or is_dev_mode():
            body["description"] = http_exc.description
        if is_dev_mode():
            body["traceback"] = "".join(traceback.format_exception(exc))
        body.update(getattr(exc, "rest_json_info", None) or {})
        return body

    def _log(self, exc, http_exc, body):
        """Log the error with the request details, w/o secrets."""
        request = self.request
        if not request:
            return
        extra = self._log_prepare_data(exc, http_exc, body)
        _logger.error(
            "http_api_call to url %s with method %s and params %s "
            "raise the following error %s",
            extra["url"],
            extra["method"],
            extra["params"],
            exc,
            extra=extra,
            exc_info=http_exc.code >= 500,
        )

    def _log_prepare_data(self, exc, http_exc, body):
        """Return the data to log for the current request.

        Secrets are removed and every value is truncated:
        params, headers and the body come from the client
        (or echo it) and could be used to flood the logs.
        """
        httprequest = self.request.httprequest
        headers = {
            k: v
            for k, v in httprequest.headers.items()
            if k not in BLACKLISTED_LOG_HEADERS
        }
        params = dict(getattr(self.request, "params", None) or {})
        for k in params:
            if k in BLACKLISTED_LOG_PARAMS:
                params[k] = "<redacted>"
        return {
            "application": "REST Services",
            "url": httprequest.url,
            "method": httprequest.method,
            "params": self._log_truncate(params),
            "headers": self._log_truncate(headers),
            "status": http_exc.code,
            "exception_body": self._log_truncate(body),
        }

    def _log_truncate(self, value):
        """Return value w/ strings (nested ones too) cut to `LOG_MAX_VALUE_LENGTH`."""
        if isinstance(value, dict):
            return {k: self._log_truncate(v) for k, v in value.items()}
        if isinstance(value, list | tuple):
            return [self._log_truncate(v) for v in value]
        if isinstance(value, str) and len(value) > LOG_MAX_VALUE_LENGTH:
            return value[:LOG_MAX_VALUE_LENGTH] + "<truncated>"
        return value
