# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import traceback

from werkzeug.urls import url_encode, url_join

from odoo import exceptions, registry
from odoo.http import request

from odoo.addons.component.core import AbstractComponent


class RESTServiceDispatchException(Exception):

    rest_json_info = {}

    def __init__(self, message, log_entry_url):
        super().__init__(message)
        self.rest_json_info = {"log_entry_url": log_entry_url}


class RESTServiceUserErrorException(RESTServiceDispatchException, exceptions.UserError):
    """User error wrapped exception."""


class RESTServiceValidationErrorException(
    RESTServiceDispatchException, exceptions.ValidationError
):
    """Validation error wrapped exception."""


class BaseRESTService(AbstractComponent):
    _inherit = "base.rest.service"
    # can be overridden to disable logging of requests to DB
    _log_calls_in_db = True

    def dispatch(self, method_name, *args, params=None):
        if not self._db_logging_active():
            return super().dispatch(method_name, *args, params=params)
        return self._dispatch_with_db_logging(method_name, *args, params=params)

    def _db_logging_active(self):
        return (
            request and self._log_calls_in_db and self.env["rest.log"].logging_active()
        )

    def _dispatch_with_db_logging(self, method_name, *args, params=None):
        try:
            result = super().dispatch(method_name, *args, params=params)
        except exceptions.UserError as orig_exception:
            self._dispatch_exception(
                RESTServiceUserErrorException, orig_exception, *args, params=params
            )
        except exceptions.ValidationError as orig_exception:
            self._dispatch_exception(
                RESTServiceValidationErrorException,
                orig_exception,
                *args,
                params=params,
            )
        except Exception as orig_exception:
            self._dispatch_exception(
                RESTServiceDispatchException, orig_exception, *args, params=params
            )
        log_entry = self._log_call_in_db(
            self.env, request, *args, params=params, result=result
        )
        log_entry_url = self._get_log_entry_url(log_entry)
        result["log_entry_url"] = log_entry_url
        return result

    def _dispatch_exception(self, exception_klass, orig_exception, *args, params=None):
        tb = traceback.format_exc()
        # TODO: how to test this? Cannot rollback nor use another cursor
        self.env.cr.rollback()
        with registry(self.env.cr.dbname).cursor() as cr:
            env = self.env(cr=cr)
            log_entry = self._log_call_in_db(
                env,
                request,
                *args,
                params=params,
                traceback=tb,
                orig_exception=orig_exception,
            )
            log_entry_url = self._get_log_entry_url(log_entry)
        # UserError and alike have `name` attribute to store the msg
        exc_msg = self._get_exception_message(orig_exception)
        raise exception_klass(exc_msg, log_entry_url) from orig_exception

    def _get_exception_message(self, exception):
        return getattr(exception, "name", str(exception))

    def _get_log_entry_url(self, entry):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url_params = {
            "action": self.env.ref("rest_log.action_rest_log").id,
            "view_type": "form",
            "model": entry._name,
            "id": entry.id,
        }
        url = "/web?#%s" % url_encode(url_params)
        return url_join(base_url, url)

    @property
    def _log_call_header_strip(self):
        return ("Cookie", "Api-Key")

    def _log_call_in_db_values(self, _request, *args, params=None, **kw):
        httprequest = _request.httprequest
        headers = dict(httprequest.headers)
        for header_key in self._log_call_header_strip:
            if header_key in headers:
                headers[header_key] = "<redacted>"
        if args:
            params = dict(params or {}, args=args)

        result = kw.get("result")
        error = kw.get("traceback")
        orig_exception = kw.get("orig_exception")
        exception_name = None
        exception_message = None
        if orig_exception:
            exception_name = orig_exception.__class__.__name__
            if hasattr(orig_exception, "__module__"):
                exception_name = orig_exception.__module__ + "." + exception_name
            exception_message = self._get_exception_message(orig_exception)
        return {
            "request_url": httprequest.url,
            "request_method": httprequest.method,
            "params": json.dumps(params, indent=4, sort_keys=True),
            "headers": json.dumps(headers, indent=4, sort_keys=True),
            "result": json.dumps(result, indent=4, sort_keys=True),
            "error": error,
            "exception_name": exception_name,
            "exception_message": exception_message,
            "state": "success" if result else "failed",
        }

    def _log_call_in_db(self, env, _request, *args, params=None, **kw):
        values = self._log_call_in_db_values(_request, *args, params=params, **kw)
        if not values:
            return
        return env["rest.log"].sudo().create(values)
