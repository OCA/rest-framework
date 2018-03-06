# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging
import sys
import traceback
import datetime
from odoo.exceptions import (
    UserError, MissingError, AccessError, AccessDenied, ValidationError)
from odoo.http import HttpRequest, Root, request
from werkzeug.exceptions import BadRequest, NotFound, Forbidden, \
    InternalServerError, HTTPException
from werkzeug.utils import escape
from .core import _rest_services_databases

_logger = logging.getLogger(__name__)

try:
    import pyquerystring
except (ImportError, IOError) as err:
    _logger.debug(err)


class JSONEncoder(json.JSONEncoder):

    def default(self, obj):  # pylint: disable=E0202
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        return super(JSONEncoder, self).default(obj)


def wrapJsonException(exception):
    """Wrapper method that modify the exception in order
    to render it like a json"""

    get_original_headers = exception.get_headers

    def get_body(environ=None):
        return JSONEncoder().encode({
            'code': exception.code,
            'name': escape(exception.name),
            'description': exception.get_description(environ)
            })

    def get_headers(environ=None):
        """Get a list of headers."""
        _headers = [('Content-Type', 'application/json')]
        for key, value in get_original_headers(environ=environ):
            if key != 'Content-Type':
                _headers.append(key, value)
        return _headers

    exception.get_body = get_body
    exception.get_headers = get_headers
    if request:
        httprequest = request.httprequest
        headers = dict(httprequest.headers)
        headers.pop('Api-Key', None)
        message = (
            'RESTFULL call to url %s with method %s and params %s '
            'raise the following error %s')
        args = (httprequest.url, httprequest.method, request.params, exception)
        extra = {
            'application': 'REST Services',
            'url': httprequest.url,
            'method': httprequest.method,
            'params': request.params,
            'headers': headers,
            'status': exception.code,
            'exception_body': exception.get_body(),
            'traceback': ''.join(traceback.format_exception(*sys.exc_info())),
            }
        _logger.error(message, *args, extra=extra)
    return exception


class HttpRestRequest(HttpRequest):
    """Http request that always return json, usefull for rest api"""

    def __init__(self, httprequest):
        super(HttpRestRequest, self).__init__(httprequest)
        if self.httprequest.mimetype == 'application/json':
            self.params = json.loads(self.httprequest.data)
        else:
            # We reparse the query_string in order to handle data structure
            # more information on https://github.com/aventurella/pyquerystring
            self.params = pyquerystring.parse(self.httprequest.query_string)
        lang = self.httprequest.headers.get('Lang')
        if lang:
            self._context = self._context or {}
            self._context['lang'] = lang

    def _handle_exception(self, exception):
        """Called within an except block to allow converting exceptions
           to abitrary responses. Anything returned (except None) will
           be used as response."""
        try:
            return super(HttpRestRequest, self)._handle_exception(exception)
        except (UserError, ValidationError), e:
            return wrapJsonException(
                BadRequest(e.message or e.value or e.name))
        except MissingError, e:
            return wrapJsonException(NotFound(e.value))
        except (AccessError, AccessDenied), e:
            return wrapJsonException(Forbidden(e.message))
        except HTTPException, e:
            return wrapJsonException(e)
        except:  # flake8: noqa: E722
            return wrapJsonException(InternalServerError())

    def make_json_response(self, data, headers=None, cookies=None):
        data = JSONEncoder().encode(data)
        if headers is None:
            headers = {}
        headers['Content-Type'] = 'application/json'
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
