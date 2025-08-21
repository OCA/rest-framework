# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import json
import time
from traceback import format_exception

from werkzeug.exceptions import HTTPException as WerkzeugHTTPException

from odoo import api, fields, models


class APILog(models.Model):
    _name = "api.log"
    _description = "Log for API"
    _order = "id desc"

    collection_ref = fields.Reference(
        selection="_selection_collection_ref",
    )
    collection_model = fields.Char(
        compute="_compute_collection",
        store=True,
        index=True,
    )
    collection_id = fields.Integer(
        compute="_compute_collection",
        store=True,
        index=True,
    )

    # Request
    request_url = fields.Char()
    request_method = fields.Char()
    request_headers = fields.Json()
    request_body = fields.Binary(attachment=False)
    request_date = fields.Datetime()
    request_time = fields.Float()

    # Response
    response_status_code = fields.Integer()
    response_headers = fields.Json()
    response_body = fields.Binary(attachment=False)
    response_date = fields.Datetime()
    response_time = fields.Float()

    stack_trace = fields.Text()

    # Derived fields
    name = fields.Char(compute="_compute_name", store=True)
    time = fields.Float(compute="_compute_time", store=True)
    request_preview = fields.Text(compute="_compute_request_preview")
    response_preview = fields.Text(compute="_compute_response_preview")
    # Binary fields are useful to download the payload in case of file download/upload
    request_b64 = fields.Binary(
        string="Request Content", compute="_compute_request_b64"
    )
    response_b64 = fields.Binary(
        string="Response Content", compute="_compute_response_b64"
    )
    request_headers_preview = fields.Text(compute="_compute_headers_preview")
    response_headers_preview = fields.Text(compute="_compute_headers_preview")
    request_content_type = fields.Char(
        compute="_compute_request_headers_derived", store=True
    )
    request_content_length = fields.Integer(
        compute="_compute_request_headers_derived", store=True
    )
    referrer = fields.Char(compute="_compute_request_headers_derived", store=True)
    response_content_type = fields.Char(
        compute="_compute_response_headers_derived", store=True
    )
    response_content_length = fields.Integer(
        compute="_compute_response_headers_derived", store=True
    )

    @api.model
    def _selection_collection_ref(self):
        return []

    @api.depends(
        "collection_ref",
    )
    def _compute_collection(self):
        for log in self:
            collection = log.collection_ref
            if collection:
                collection_model = collection._name
                collection_id = collection.id
            else:
                collection_model = False
                collection_id = False
            log.collection_model = collection_model
            log.collection_id = collection_id

    @api.model
    def _headers_hidden_keys(self):
        """Header keys that should not be logged.

        They might contains sensitive data.
        """
        return (
            "Api-Key",
            "Cookie",
        )

    @api.model
    def _sanitize_headers_dict(self, headers_dict):
        keys_to_hide = self._headers_hidden_keys()
        for key in headers_dict:
            if key in keys_to_hide:
                headers_dict[key] = "<redacted>"
        return headers_dict

    @api.model
    def _headers_to_dict(self, headers):
        headers_dict = {key: value for key, value in headers.items()}
        return self._sanitize_headers_dict(headers_dict)

    def _current_time(self):
        return time.time_ns() / 1e9

    @api.model
    def _get_http_request(self, request):
        return request.httprequest

    @api.model
    def _get_request_body(self, request):
        """Take extra care with the request's body because it might get consumed."""
        httprequest = self._get_http_request(request)
        return httprequest.data

    @api.model
    def _prepare_log_request(self, request):
        httprequest = self._get_http_request(request)
        log_request_values = {
            "request_url": httprequest.url,
            "request_method": httprequest.method,
            "request_headers": self._headers_to_dict(httprequest.headers),
            "request_body": self._get_request_body(request),
            "request_date": fields.Datetime.now(),
            "request_time": self._current_time(),
        }
        return log_request_values

    @api.model
    def log_request(self, request, override_log_values=None):
        log_request_values = self._prepare_log_request(request)
        log_request_values.update(override_log_values or {})
        return self.sudo().create(log_request_values)

    def _inject_log_entry(self, values_dict):
        values_dict["API-Log-Entry-ID"] = str(self.id)
        return values_dict

    def _prepare_log_response(self, response):
        self._inject_log_entry(response.headers)
        headers_dict = self._headers_to_dict(response.headers)
        return {
            "response_status_code": response.status_code,
            "response_headers": headers_dict,
            "response_body": response.data,
            "response_date": fields.Datetime.now(),
            "response_time": self._current_time(),
        }

    def log_response(self, response):
        log_response_values = self._prepare_log_response(response)
        return self.sudo().write(log_response_values)

    def _prepare_log_exception(self, exception):
        exception.headers = getattr(exception, "headers", {})
        values = {
            "stack_trace": "".join(format_exception(exception)),
            "response_headers": self._inject_log_entry(exception.headers),
            "response_body": str(exception),
            "response_date": fields.Datetime.now(),
            "response_time": self._current_time(),
        }

        if isinstance(exception, WerkzeugHTTPException):
            values.update(
                {
                    "response_status_code": exception.code,
                    "response_headers": self._headers_to_dict(exception.get_headers()),
                    "response_body": exception.get_body(),
                }
            )
        return values

    def log_exception(self, exception):
        try:
            exc_handling_response = self.env.registry["ir.http"]._handle_error(
                exception
            )
            self.log_response(exc_handling_response)
        except Exception as handling_exception:
            exception = handling_exception
        log_exception_values = self._prepare_log_exception(exception)
        return self.sudo().write(log_exception_values)

    @api.depends("request_url", "request_method", "request_date")
    def _compute_name(self):
        for log in self:
            log.name = (
                f"{log.request_date.isoformat()} - "
                f"[{log.request_method}] {log.request_url}"
            )

    @api.depends("request_time", "response_time")
    def _compute_time(self):
        for log in self:
            if log.request_time and log.response_time:
                log.time = log.response_time - log.request_time
            else:
                log.time = 0

    @api.depends("request_headers")
    def _compute_request_headers_derived(self):
        for log in self:
            headers = log.request_headers or {}
            log.request_content_type = headers.get("content-type", "")
            log.request_content_length = headers.get("content-length", 0)
            log.referrer = headers.get("referer", "")

    @api.depends("response_headers")
    def _compute_response_headers_derived(self):
        for log in self:
            headers = log.response_headers or {}
            log.response_content_type = headers.get("content-type", "")
            log.response_content_length = headers.get("content-length", 0)

    @api.depends("request_body")
    def _compute_request_preview(self):
        for log in self.with_context(bin_size=False):
            log.request_preview = log._body_preview(log.request_body)

    @api.depends("response_body")
    def _compute_response_preview(self):
        for log in self.with_context(bin_size=False):
            log.response_preview = log._body_preview(log.response_body)

    def _body_preview(self, body):
        # Display the first 1000 characters of the body if it's a text content
        body_preview = False
        if body:
            try:
                body_preview = body.decode("utf-8", errors="ignore")
                if len(body_preview) > 1000:
                    body_preview = body_preview[:1000] + "...\n(...)"
            except UnicodeDecodeError:
                body_preview = False
        return body_preview

    @api.depends("request_headers", "response_headers")
    def _compute_headers_preview(self):
        for log in self:
            log.request_headers_preview = log._headers_preview(log.request_headers)
            log.response_headers_preview = log._headers_preview(log.response_headers)

    def _headers_preview(self, headers):
        return json.dumps(headers, sort_keys=True, indent=4) if headers else False

    @api.depends("request_body")
    def _compute_request_b64(self):
        for log in self:
            log.request_b64 = base64.b64encode(log.request_body or b"")

    @api.depends("response_body")
    def _compute_response_b64(self):
        for log in self:
            log.response_b64 = base64.b64encode(log.response_body or b"")
