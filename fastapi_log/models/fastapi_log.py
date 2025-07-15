# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import json
import time
from traceback import format_exception

from starlette.exceptions import HTTPException as StarletteHTTPException
from werkzeug.exceptions import HTTPException as WerkzeugHTTPException

from odoo import api, fields, models


class FastapiLog(models.Model):
    _name = "fastapi.log"
    _description = "Fastapi Log"
    _order = "id desc"

    endpoint_id = fields.Many2one(
        "fastapi.endpoint",
        string="Endpoint",
        required=True,
        ondelete="cascade",
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

    def _headers_to_dict(self, headers):
        try:
            return {key.lower(): value for key, value in headers.items()}
        except AttributeError:
            return {}

    def _current_time(self):
        return time.time_ns() / 1e9

    @api.model
    def log_request(self, request, environ, endpoint_id):
        body = None
        # Be careful to not consume the request body if it hasn't been wrapped
        stream = environ.get("wsgi.input")
        if stream and stream.seekable():
            body = stream.read()
            stream.seek(0)

        return self.create(
            {
                "endpoint_id": endpoint_id,
                "request_url": request.url,
                "request_method": request.method,
                "request_headers": self._headers_to_dict(request.headers),
                "request_body": body,
                "request_date": fields.Datetime.now(),
                "request_time": self._current_time(),
            }
        )

    @api.model
    def log_response(self, response):
        return self.write(
            {
                "response_status_code": response.status_code,
                "response_headers": self._headers_to_dict(response.headers),
                "response_body": response.data,
                "response_date": fields.Datetime.now(),
                "response_time": self._current_time(),
            }
        )

    @api.model
    def log_exception(self, exception):
        self.write(
            {
                "stack_trace": "".join(format_exception(exception)),
            }
        )
        if isinstance(exception, StarletteHTTPException):
            return self.write(
                {
                    "response_status_code": exception.status_code,
                    "response_headers": self._headers_to_dict(exception.headers),
                    "response_body": exception.detail,
                    "response_date": fields.Datetime.now(),
                    "response_time": self._current_time(),
                }
            )
        if isinstance(exception, WerkzeugHTTPException):
            return self.write(
                {
                    "response_status_code": exception.code,
                    "response_headers": self._headers_to_dict(exception.get_headers()),
                    "response_body": exception.get_body(),
                    "response_date": fields.Datetime.now(),
                    "response_time": self._current_time(),
                }
            )
        try:
            return self.log_response(
                self.env.registry["ir.http"]._handle_error(exception)
            )
        except Exception:
            return self.write(
                {
                    "response_status_code": 599,
                    "response_body": str(exception),
                    "response_date": fields.Datetime.now(),
                    "response_time": self._current_time(),
                }
            )

    @api.depends("request_url", "request_method", "request_date")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"{record.request_date.isoformat()} - "
                f"[{record.request_method} {record.request_url}"
            )

    @api.depends("request_time", "response_time")
    def _compute_time(self):
        for record in self:
            if record.request_time and record.response_time:
                record.time = record.response_time - record.request_time
            else:
                record.time = 0

    @api.depends("request_headers")
    def _compute_request_headers_derived(self):
        for record in self:
            headers = record.request_headers or {}
            record.request_content_type = headers.get("content-type", "")
            record.request_content_length = headers.get("content-length", 0)
            record.referrer = headers.get("referer", "")

    @api.depends("response_headers")
    def _compute_response_headers_derived(self):
        for record in self:
            headers = record.response_headers or {}
            record.response_content_type = headers.get("content-type", "")
            record.response_content_length = headers.get("content-length", 0)

    @api.depends("request_body")
    def _compute_request_preview(self):
        for record in self.with_context(bin_size=False):
            record.request_preview = record._body_preview(record.request_body)

    @api.depends("response_body")
    def _compute_response_preview(self):
        for record in self.with_context(bin_size=False):
            record.response_preview = record._body_preview(record.response_body)

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
        for record in self:
            record.request_headers_preview = record._headers_preview(
                record.request_headers
            )
            record.response_headers_preview = record._headers_preview(
                record.response_headers
            )

    def _headers_preview(self, headers):
        return json.dumps(headers, sort_keys=True, indent=4) if headers else False

    @api.depends("request_body")
    def _compute_request_b64(self):
        self.request_b64 = base64.b64encode(self.request_body or b"")

    @api.depends("response_body")
    def _compute_response_b64(self):
        self.response_b64 = base64.b64encode(self.response_body or b"")
