# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from types import SimpleNamespace
from unittest import mock

from werkzeug.test import EnvironBuilder

from odoo.tests.common import BaseCase

from ..call import ApiCall


def _call(path="/", method="GET", data=None, content_type=None, routing=None):
    builder = EnvironBuilder(
        path=path, method=method, data=data, content_type=content_type
    )
    request = SimpleNamespace(httprequest=builder.get_request())
    endpoint = SimpleNamespace(routing=routing or {})
    return ApiCall(request=request, endpoint=endpoint, args={})


class TestApiCall(BaseCase):
    def test_query_only_does_not_parse_body(self):
        """Reading the query never parses the body."""
        body = json.dumps({"a": 1})
        call = _call("/?q=x", "POST", body, "application/json")
        with mock.patch(
            "odoo.addons.http_api_dispatcher.call.read_body",
            wraps=lambda *a, **kw: {},
        ) as read_body:
            self.assertEqual(call.query, {"q": "x"})
        read_body.assert_not_called()

    def test_body_parsed_once(self):
        """The body is parsed on first access and the same dict is reused."""
        body = json.dumps({"a": "1"})
        call = _call("/", "POST", body, "application/json")
        with mock.patch(
            "odoo.addons.http_api_dispatcher.call.read_body",
            wraps=lambda *a, **kw: {"a": "1"},
        ) as read_body:
            self.assertEqual(call.body, {"a": "1"})
            self.assertEqual(call.body, {"a": "1"})
        read_body.assert_called_once()

    def test_params_precedence(self):
        """Params merge query, then body, then URL args: the last one wins."""
        body = json.dumps({"a": "body", "b": "body"})
        call = _call("/?a=query&c=query", "POST", body, "application/json")
        call.args = {"b": "url"}
        self.assertEqual(call.params, {"a": "body", "b": "url", "c": "query"})
        self.assertIs(call.params, call.params)

    def test_body_parsers_route_key(self):
        """A route overrides the body parser of a mimetype via `body_parsers`."""
        body = "<item/>"
        routing = {"body_parsers": {"application/xml": lambda req: {"xml": True}}}
        call = _call("/", "POST", body, "application/xml", routing=routing)
        self.assertEqual(call.body, {"xml": True})

    def test_query_parser_route_key(self):
        """A route overrides the query parser via `query_parser`."""
        routing = {"query_parser": lambda req: {"custom": "1"}}
        call = _call("/?a=1", routing=routing)
        self.assertEqual(call.query, {"custom": "1"})

    def test_params_sync_request(self):
        """The merged params are exposed on the request, for error logs."""
        call = _call("/?a=1")
        self.assertFalse(hasattr(call.request, "params"))
        self.assertEqual(call.params, {"a": "1"})
        self.assertEqual(call.request.params, {"a": "1"})
