# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import json
import logging
import traceback

from psycopg2.errors import OperationalError
from werkzeug.urls import url_encode, url_join

from odoo import exceptions
from odoo.http import Response, request
from odoo.modules.registry import Registry
from odoo.service.model import PG_CONCURRENCY_ERRORS_TO_RETRY

from odoo.addons.base_rest.http import JSONEncoder
from odoo.addons.component.core import AbstractComponent

from ..exceptions import (
    RESTServiceDispatchException,
    RESTServiceMissingErrorException,
    RESTServiceUserErrorException,
    RESTServiceValidationErrorException,
)

_logger = logging.getLogger(__name__)


def json_dump(data):
    """Encode data to JSON as we like."""
    return json.dumps(data, cls=JSONEncoder, indent=4, sort_keys=True, default=str)


class BaseRESTService(AbstractComponent):
    _inherit = "base.rest.service"
    # can be overridden to enable logging of requests to DB
    _log_calls_in_db = False

    def dispatch(self, method_name, *args, params=None):
        if not self._db_logging_active(method_name):
            return super().dispatch(method_name, *args, params=params)
        return self._dispatch_with_db_logging(method_name, *args, params=params)

    def _dispatch_with_db_logging(self, method_name, *args, params=None):
        try:
            with self.env.cr.savepoint():
                result = super().dispatch(method_name, *args, params=params)
        except exceptions.MissingError as orig_exception:
            self._dispatch_exception(
                method_name,
                RESTServiceMissingErrorException,
                orig_exception,
                *args,
                params=params,
            )
        except exceptions.ValidationError as orig_exception:
            self._dispatch_exception(
                method_name,
                RESTServiceValidationErrorException,
                orig_exception,
                *args,
                params=params,
            )
        except exceptions.UserError as orig_exception:
            self._dispatch_exception(
                method_name,
                RESTServiceUserErrorException,
                orig_exception,
                *args,
                params=params,
            )
        except Exception as orig_exception:
            self._dispatch_exception(
                method_name,
                RESTServiceDispatchException,
                orig_exception,
                *args,
                params=params,
            )
        self._log_dispatch_success(method_name, result, *args, params)
        return result

    def _log_dispatch_success(self, method_name, result, *args, params=None):
        try:
            with self.env.cr.savepoint():
                log_entry = self._log_call_in_db(
                    self.env, request, method_name, *args, params, result=result
                )
                if log_entry and not isinstance(result, Response):
                    log_entry_url = self._get_log_entry_url(log_entry)
                    result["log_entry_url"] = log_entry_url
        except Exception as e:
            _logger.exception("Rest Log Error Creation: %s", e)

    def _dispatch_exception(
        self, method_name, exception_klass, orig_exception, *args, params=None
    ):
        exc_msg, log_entry_url = None, None  # in case it fails below
        try:
            exc_msg = self._get_exception_message(orig_exception)
            tb = traceback.format_exc()
            with Registry(self.env.cr.dbname).cursor() as cr:
                log_entry = self._log_call_in_db(
                    self.env(cr=cr),
                    request,
                    method_name,
                    *args,
                    params=params,
                    traceback=tb,
                    orig_exception=orig_exception,
                )
                log_entry_url = self._get_log_entry_url(log_entry)
        except Exception as e:
            _logger.exception("Rest Log Error Creation: %s", e)
        # let the OperationalError bubble up to the retrying mechanism
        # We can't wrap the OperationalError because we want to let it
        # bubble up to the retrying mechanism, it will be handled by
        # the default handler at the end of the chain.
        if (
            isinstance(orig_exception, OperationalError)
            and orig_exception.pgcode in PG_CONCURRENCY_ERRORS_TO_RETRY
        ):
            raise orig_exception
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
        url = f"/web?#{url_encode(url_params)}"
        return url_join(base_url, url)

    @property
    def _log_call_header_strip(self):
        return ("Cookie", "Api-Key")

    def _log_call_in_db_values(self, _request, *args, params=None, **kw):
        httprequest = _request.httprequest
        headers = self._log_call_sanitize_headers(dict(httprequest.headers or []))
        params = dict(params or {})
        if args:
            params.update(args=args)
        params = self._log_call_sanitize_params(params)
        error, exception_name, exception_message = self._log_call_prepare_error(**kw)
        result, state = self._log_call_prepare_result(kw.get("result"))
        collection = self.work.collection
        return {
            "collection": collection._name,
            "collection_id": collection.id,
            "request_url": httprequest.url,
            "request_method": httprequest.method,
            "params": params,
            "headers": headers,
            "result": result,
            "error": error,
            "exception_name": exception_name,
            "exception_message": exception_message,
            "state": state,
        }

    def _log_call_prepare_result(self, result):
        # NB: ``result`` might be an object of class ``odoo.http.Response``,
        # for example when you try to download a file. In this case, we need to
        # handle it properly, without the assumption that ``result`` is a dict.
        if isinstance(result, Response):
            status_code = result.status_code
            result = {
                "status": status_code,
                "headers": self._log_call_sanitize_headers(dict(result.headers or [])),
            }
            state = "success" if status_code in range(200, 300) else "failed"
        else:
            state = "success" if result else "failed"
        return result, state

    def _log_call_prepare_error(self, traceback=None, orig_exception=None, **kw):
        exception_name = None
        exception_message = None
        if orig_exception:
            exception_name = orig_exception.__class__.__name__
            if hasattr(orig_exception, "__module__"):
                exception_name = orig_exception.__module__ + "." + exception_name
            exception_message = self._get_exception_message(orig_exception)
        return traceback, exception_name, exception_message

    _log_call_in_db_keys_to_serialize = ("params", "headers", "result")

    def _log_call_in_db(self, env, _request, method_name, *args, params=None, **kw):
        values = self._log_call_in_db_values(_request, *args, params=params, **kw)
        for k in self._log_call_in_db_keys_to_serialize:
            values[k] = json_dump(values[k])
        enabled_states = self._get_matching_active_conf(method_name)
        if not values or enabled_states and values["state"] not in enabled_states:
            return
        return env["rest.log"].sudo().create(values)

    def _log_call_sanitize_params(self, params: dict) -> dict:
        if "password" in params:
            params["password"] = "<redacted>"
        return params

    def _log_call_sanitize_headers(self, headers: dict) -> dict:
        for header_key in self._log_call_header_strip:
            if header_key in headers:
                headers[header_key] = "<redacted>"
        return headers

    def _db_logging_active(self, method_name):
        enabled = self._log_calls_in_db
        if not enabled:
            enabled = bool(self._get_matching_active_conf(method_name))
        return request and enabled and self.env["rest.log"].logging_active()

    def _get_matching_active_conf(self, method_name):
        return self.env["rest.log"]._get_matching_active_conf(
            self._collection, self._usage, method_name
        )
