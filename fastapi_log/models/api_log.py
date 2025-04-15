# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from starlette.exceptions import HTTPException as StarletteHTTPException

from odoo import api, fields, models


class FastapiLog(models.Model):
    _inherit = "api.log"

    fastapi_endpoint_id = fields.Many2one(
        comodel_name="fastapi.endpoint",
        string="Endpoint",
        ondelete="cascade",
        index=True,
    )

    @api.model
    def _get_request_body(self, request):
        # Be careful to not consume the request body if it hasn't been wrapped
        dispatcher = request.dispatcher
        if dispatcher.routing_type == "fastapi":
            environ = dispatcher._get_environ()
            stream = environ.get("wsgi.input")
            if stream and stream.seekable():
                request_body = stream.read()
                stream.seek(0)
        else:
            request_body = super()._get_request_body(request)
        return request_body

    @api.model
    def _prepare_log_request(self, request):
        log_request_values = super()._prepare_log_request(request)
        dispatcher = request.dispatcher
        if dispatcher.routing_type == "fastapi":
            environ = dispatcher._get_environ()
            endpoint = (
                request.env["fastapi.endpoint"]
                .sudo()
                ._get_endpoint(environ["PATH_INFO"])
            )
            log_request_values["fastapi_endpoint_id"] = endpoint.id
        return log_request_values

    def _prepare_log_exception(self, exception):
        values = super()._prepare_log_exception(exception)
        if isinstance(exception, StarletteHTTPException):
            values.update(
                {
                    "response_status_code": exception.status_code,
                    "response_headers": self._headers_to_dict(exception.headers),
                    "response_body": exception.detail,
                }
            )
        return values
