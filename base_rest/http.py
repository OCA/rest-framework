# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
import json
import logging
import sys
import traceback
from collections import defaultdict

from werkzeug.exceptions import (
    BadRequest,
    Forbidden,
    HTTPException,
    InternalServerError,
    NotFound,
    Unauthorized,
)
from werkzeug.utils import escape

from odoo.exceptions import (
    AccessDenied,
    AccessError,
    MissingError,
    UserError,
    ValidationError,
)
from odoo.http import HttpRequest, Root, SessionExpiredException, request
from odoo.tools import ustr
from odoo.tools.config import config

from .core import _rest_services_databases

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
        return super(JSONEncoder, self).default(obj)


def wrapJsonException(exception, include_description=False, extra_info=None):
    """Wrap exceptions to be rendered as JSON.

    :param exception: an instance of an exception
    :param include_description: include full description in payload
    :param extra_info: dict to provide extra keys to include in payload
    """

    get_original_headers = exception.get_headers
    exception.traceback = "".join(traceback.format_exception(*sys.exc_info()))

    def get_body(environ=None):
        res = {"code": exception.code, "name": escape(exception.name)}
        description = exception.get_description(environ)
        if config.get_misc("base_rest", "dev_mode"):
            # return exception info only if base_rest is in dev_mode
            res.update({"traceback": exception.traceback, "description": description})
        elif include_description:
            res["description"] = description
        res.update(extra_info or {})
        return JSONEncoder().encode(res)

    def get_headers(environ=None):
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
        args = (httprequest.url, httprequest.method, request.params, exception)
        extra = {
            "application": "REST Services",
            "url": httprequest.url,
            "method": httprequest.method,
            "params": request.params,
            "headers": headers,
            "status": exception.code,
            "exception_body": exception.get_body(),
        }
        _logger.exception(message, *args, extra=extra)
    return exception


class HttpRestRequest(HttpRequest):
    """Http request that always return json, usefull for rest api"""

    def __init__(self, httprequest):
        super(HttpRestRequest, self).__init__(httprequest)
        if self.httprequest.mimetype == "application/json":
            data = self.httprequest.get_data().decode(self.httprequest.charset)
            self.params = json.loads(data)
        else:
            # We reparse the query_string in order to handle data structure
            # more information on https://github.com/aventurella/pyquerystring
            self.params = pyquerystring.parse(
                self.httprequest.query_string.decode("utf-8")
            )
        self._determine_context_lang()

    def _determine_context_lang(self):
        """
        In this function, we parse the preferred languages specified into the
        'Accept-language' http header. The lang into the context is initialized
        according to the priority of languages into the headers and those
        available into Odoo.
        """
        accepted_langs = self.httprequest.headers.get("Accept-language")
        if not accepted_langs:
            return
        parsed_accepted_langs = parse_accept_language(accepted_langs)
        installed_locale_langs = set()
        installed_locale_by_lang = defaultdict(list)
        for lang_code, _name in self.env["res.lang"].get_installed():
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
                context = dict(self._context)
                context["lang"] = locale
                # the setter defiend in odoo.http.WebRequest reset the env
                # when setting a new context
                self.context = context
                break

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to abitrary responses. Anything returned (except None) will
           be used as response."""
        if isinstance(exception, SessionExpiredException):
            # we don't want to return the login form as plain html page
            # we want to raise a proper exception
            return wrapJsonException(Unauthorized(ustr(exception)))
        try:
            return super(HttpRestRequest, self)._handle_exception(exception)
        except (UserError, ValidationError) as e:
            return wrapJsonException(BadRequest(e.name), include_description=True)
        except MissingError as e:
            return wrapJsonException(NotFound(ustr(e)))
        except (AccessError, AccessDenied) as e:
            return wrapJsonException(Forbidden(ustr(e)))
        except HTTPException as e:
            return wrapJsonException(e)
        except Exception as e:  # flake8: noqa: E722
            extra_info = getattr(e, "rest_json_info", None)
            return wrapJsonException(InternalServerError(e), extra_info=extra_info)

    def make_json_response(self, data, headers=None, cookies=None):
        data = JSONEncoder().encode(data)
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        return self.make_response(data, headers=headers, cookies=cookies)


ori_get_request = Root.get_request


def get_request(self, httprequest):
    db = httprequest.session.db
    service_registry = _rest_services_databases.get(db)
    if service_registry:
        for root_path in service_registry:
            if httprequest.path.startswith(root_path):
                return HttpRestRequest(httprequest)
    return ori_get_request(self, httprequest)


Root.get_request = get_request
