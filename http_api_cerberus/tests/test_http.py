# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from odoo import http
from odoo.tests.common import HttpCase, tagged
from odoo.tools import mute_logger

from ..params import CerberusParam


class CerberusTestController(http.Controller):
    def _get_input_schema(self):
        return {"name": {"type": "string", "required": True}}

    @http.route(
        "/http_api_cerberus_test/hello",
        type="http_api",
        auth="public",
        csrf=False,
        methods=["POST"],
        input=CerberusParam("_get_input_schema"),
        output=CerberusParam({"greeting": {"type": "string", "required": True}}),
    )
    def hello(self, name):
        return {"greeting": f"Hello {name}", "secret": "dropped"}


@tagged("-at_install", "post_install")
class TestHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.registry.clear_cache("routing")

    def _post(self, data):
        return self.url_open(
            "/http_api_cerberus_test/hello",
            data=json.dumps(data),
            headers={"Content-Type": "application/json"},
        )

    def test_ok(self):
        """A valid request is served; keys outside the schemas are dropped."""
        response = self._post({"name": "John", "other": 1})
        self.assertEqual(response.json(), {"greeting": "Hello John"})

    @mute_logger("odoo.addons.http_api_dispatcher.errors", "odoo.http")
    def test_bad_request(self):
        """Invalid input gives a 400 w/ the Cerberus errors."""
        response = self._post({})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["errors"], {"name": ["required field"]})
