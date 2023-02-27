# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
import decimal
import json
import logging
import sys
import traceback
from collections import defaultdict

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
from odoo.http import (
    CSRF_FREE_METHODS,
    MISSING_CSRF_WARNING,
    Dispatcher,
    SessionExpiredException,
    request,
)
from odoo.tools import ustr
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

try:
    import pyquerystring
    from accept_language import parse_accept_language
except (ImportError, IOError) as err:
    _logger.debug(err)


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):  # pylint: disable=E0202,arguments-differ
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        return super(JSONEncoder, self).default(obj)


BLACKLISTED_LOG_PARAMS = ("password",)


def wrapJsonException(exception, include_description=False, extra_info=None):
    """Wrap exceptions to be rendered as JSON.

    :param exception: an instance of an exception
    :param include_description: include full description in payload
    :param extra_info: dict to provide extra keys to include in payload
    """

    get_original_headers = exception.get_headers
    exception.traceback = "".join(traceback.format_exception(*sys.exc_info()))

    def get_body(environ=None, scope=None):
        res = {"code": exception.code, "name": escape(exception.name)}
        description = exception.get_description(environ)
        if config.get_misc("base_rest", "dev_mode"):
            # return exception info only if base_rest is in dev_mode
            res.update({"traceback": exception.traceback, "description": description})
        elif include_description:
            res["description"] = description
        res.update(extra_info or {})
        return JSONEncoder().encode(res)

    def get_headers(environ=None, scope=None):
        """Get a list of headers."""
        _headers = [("Content-Type", "application/json")]
        for key, value in get_original_headers(environ=environ):
            if key != "Content-Type":
                _headers.append(key, value)
        return _headers

    exception.get_body = get_body
    exception.get_headers = get_headers
    if request:
        httprequest = request.httprequest
        headers = dict(httprequest.headers)
        headers.pop("Api-Key", None)
        message = (
            "RESTFULL call to url %s with method %s and params %s "
            "raise the following error %s"
        )
        params = (
            request.params.copy()
            if hasattr(request, "params")
            else request.get_http_params().copy()
        )
        for k in params.keys():
            if k in BLACKLISTED_LOG_PARAMS:
                params[k] = "<redacted>"
        args = (httprequest.url, httprequest.method, params, exception)
        extra = {
            "application": "REST Services",
            "url": httprequest.url,
            "method": httprequest.method,
            "params": params,
            "headers": headers,
            "status": exception.code,
            "exception_body": exception.get_body(),
        }
        _logger.exception(message, *args, extra=extra)
    return exception


class RestApiDispatcher(Dispatcher):
    """Dispatcher for requests at routes for restapi types"""

    routing_type = "restapi"

    def pre_dispatch(self, rule, args):
        res = super().pre_dispatch(rule, args)
        httprequest = self.request.httprequest
        self.request.params = args
        if httprequest.mimetype == "application/json":
            data = httprequest.get_data().decode(httprequest.charset)
            if data:
                try:
                    self.request.params.update(json.loads(data))
                except (ValueError, json.decoder.JSONDecodeError) as e:
                    msg = "Invalid JSON data: %s" % str(e)
                    _logger.info("%s: %s", self.request.httprequest.path, msg)
                    raise BadRequest(msg) from e
        elif httprequest.mimetype == "multipart/form-data":
            # Do not reassign self.params
            pass
        else:
            # We reparse the query_string in order to handle data structure
            # more information on https://github.com/aventurella/pyquerystring
            self.request.params.update(
                pyquerystring.parse(httprequest.query_string.decode("utf-8"))
            )
        self._determine_context_lang()
        return res

    def dispatch(self, endpoint, args):
        """Same as odoo.http.HttpDispatcher, except for the early db check"""
        params = dict(self.request.get_http_params(), **args)

        # Check for CSRF token for relevant requests
        if (
            self.request.httprequest.method not in CSRF_FREE_METHODS
            and endpoint.routing.get("csrf", True)
        ):
            token = params.pop("csrf_token", None)
            if not self.request.validate_csrf(token):
                if token is not None:
                    _logger.warning(
                        "CSRF validation failed on path '%s'",
                        self.request.httprequest.path,
                    )
                else:
                    _logger.warning(MISSING_CSRF_WARNING, request.httprequest.path)
                raise BadRequest("Session expired (invalid CSRF token)")

        if self.request.db:
            return self.request.registry["ir.http"]._dispatch(endpoint)
        else:
            return endpoint(**self.request.params)

    def _determine_context_lang(self):
        """
        In this function, we parse the preferred languages specified into the
        'Accept-language' http header. The lang into the context is initialized
        according to the priority of languages into the headers and those
        available into Odoo.
        """
        accepted_langs = self.request.httprequest.headers.get("Accept-language")
        if not accepted_langs:
            return
        parsed_accepted_langs = parse_accept_language(accepted_langs)
        installed_locale_langs = set()
        installed_locale_by_lang = defaultdict(list)
        for lang_code, _name in self.request.env["res.lang"].get_installed():
            installed_locale_langs.add(lang_code)
            installed_locale_by_lang[lang_code.split("_")[0]].append(lang_code)

        # parsed_acccepted_langs is sorted by priority (higher first)
        for lang in parsed_accepted_langs:
            # we first check if a locale (en_GB) is available into the list of
            # available locales into Odoo
            locale = None
            if lang.locale in installed_locale_langs:
                locale = lang.locale
            # if no locale language is installed, we look for an available
            # locale for the given language (en). We return the first one
            # found for this language.
            else:
                locales = installed_locale_by_lang.get(lang.language)
                if locales:
                    locale = locales[0]
            if locale:
                # reset the context to put our new lang.
                self.request.update_context(lang=locale)
                break

    @classmethod
    def is_compatible_with(cls, request):
        return True

    def handle_error(self, exception):
        """Called within an except block to allow converting exceptions
        to abitrary responses. Anything returned (except None) will
        be used as response."""
        if isinstance(exception, SessionExpiredException):
            # we don't want to return the login form as plain html page
            # we want to raise a proper exception
            return wrapJsonException(Unauthorized(ustr(exception)))
        if isinstance(exception, MissingError):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(NotFound(ustr(exception)), extra_info=extra_info)
        if isinstance(exception, (AccessError, AccessDenied)):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(Forbidden(ustr(exception)), extra_info=extra_info)
        if isinstance(exception, (UserError, ValidationError)):
            extra_info = getattr(exception, "rest_json_info", None)
            return wrapJsonException(
                BadRequest(exception.args[0]),
                include_description=True,
                extra_info=extra_info,
            )
        if isinstance(exception, HTTPException):
            return exception
        extra_info = getattr(exception, "rest_json_info", None)
        return wrapJsonException(InternalServerError(exception), extra_info=extra_info)

    def make_json_response(self, data, headers=None, cookies=None):
        data = JSONEncoder().encode(data)
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        return self.make_response(data, headers=headers, cookies=cookies)
