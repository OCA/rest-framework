# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import traceback

from werkzeug.urls import url_encode, url_join

from odoo import exceptions, registry
from odoo.http import request

from odoo.addons.component.core import AbstractComponent

from ..exceptions import (
    RESTServiceDispatchException,
    RESTServiceUserErrorException,
    RESTServiceValidationErrorException,
)


class BaseRESTService(AbstractComponent):
    _inherit = "base.rest.service"
    # can be overridden to enable logging of requests to DB
    _log_calls_in_db = False

    def dispatch(self, method_name, *args, params=None):
        if not self._db_logging_active():
            return super().dispatch(method_name, *args, params=params)
        return self._dispatch_with_db_logging(method_name, *args, params=params)

    def _dispatch_with_db_logging(self, method_name, *args, params=None):
        # TODO: consider refactoring thi using a savepoint as described here
        # https://github.com/OCA/rest-framework/pull/106#pullrequestreview-582099258
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
        if isinstance(result, dict):
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
        return exception.args and exception.args[0] or str(exception)

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

    def _db_logging_active(self):
        enabled = self._log_calls_in_db
        if not enabled:
            conf = self._get_log_active_conf()
            enabled = self._collection in conf or self._usage in conf
        return request and enabled and self.env["rest.log"].logging_active()

    def _get_log_active_param(self):
        param = self.env["ir.config_parameter"].sudo().get_param("rest.log.active")
        return param.strip() if param else ""

    def _get_log_active_conf(self):
        param = self._get_log_active_param()
        return tuple([x.strip() for x in param.split(",") if x.strip()])
