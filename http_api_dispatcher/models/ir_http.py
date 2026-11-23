# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from werkzeug.wrappers import Response as WerkzeugResponse

from odoo import models
from odoo.http import Response

from ..encoder import json_dumps


def _as_list(value):
    """Allow routing keys to hold a single value or a list."""
    if not value:
        return []
    if isinstance(value, list | tuple):
        return list(value)
    return [value]


class IrHttp(models.AbstractModel):
    """Hooks of the `http_api` pipeline.

    Each step can be extended by other modules via standard inheritance.
    """

    _inherit = "ir.http"

    @classmethod
    def _http_api_run(cls, call):
        """Run the full pipeline for the given `ApiCall`."""
        cls._http_api_prepare(call)
        cls._http_api_validate_input(call)
        call.result = cls._http_api_call(call)
        cls._http_api_validate_output(call)
        return cls._http_api_make_response(call)

    @classmethod
    def _http_api_prepare(cls, call):
        """Run the `prepare` callables of the route, if any.

        Use them to validate headers, update the context, etc.
        They run before input validation.
        """
        for prepare in _as_list(call.routing.get("prepare")):
            prepare(call)

    @classmethod
    def _http_api_validate_input(cls, call):
        """Replace raw params with the ones validated by the `input` param.

        Non dict values are passed as a single keyword (`input_kwarg`).
        """
        param = call.routing.get("input")
        if not param:
            return
        params = param.from_params(call)
        if not isinstance(params, dict):
            params = {call.routing.get("input_kwarg", "payload"): params}
        # Values from the URL always win
        call.params = dict(params, **call.args)

    @classmethod
    def _http_api_call(cls, call):
        """Call the endpoint. Wrap this to log, profile, etc."""
        call.request.params = call.params
        return cls._dispatch(call.endpoint)

    @classmethod
    def _http_api_validate_output(cls, call):
        """Validate the result via the `output` param, except for responses."""
        param = call.routing.get("output")
        if not param or isinstance(call.result, WerkzeugResponse):
            return
        call.result = param.to_response(call, call.result)

    @classmethod
    def _http_api_make_response(cls, call):
        """Return responses as they are, serialize anything else as JSON."""
        if isinstance(call.result, WerkzeugResponse):
            return call.result
        return Response(
            json_dumps(call.result, encoder=call.routing.get("json_encoder")),
            content_type="application/json",
        )
