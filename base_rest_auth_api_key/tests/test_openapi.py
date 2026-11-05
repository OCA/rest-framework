# Copyright 2026 Cal Peyser
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from apispec import APISpec

from odoo.tests.common import BaseCase

from odoo.addons.base_rest.tools import ROUTING_DECORATOR_ATTR

from ..apispec.rest_method_security_plugin import RestMethodSecurityPlugin


class TestRestMethodSecurityPlugin(BaseCase):
    def _get_spec(self, default_auth):
        spec = APISpec(
            title="test",
            version="1",
            openapi_version="3.0.0",
            plugins=[RestMethodSecurityPlugin(None)],
        )
        spec._params = {"default_auth": default_auth}
        return spec

    def _get_operation(self, spec, auth):
        routing = {"routes": ["/"], "methods": ["GET"]}
        if auth:
            routing["auth"] = auth
        spec.path("/", operations={"get": {}}, **{ROUTING_DECORATOR_ATTR: routing})
        return spec.to_dict()["paths"]["/"]["get"]

    def test_security_scheme(self):
        spec = self._get_spec("public")
        self.assertEqual(
            spec.to_dict()["components"]["securitySchemes"]["api_key"],
            {"type": "apiKey", "in": "header", "name": "API-KEY"},
        )

    def test_api_key_method(self):
        operation = self._get_operation(self._get_spec("public"), "api_key")
        self.assertEqual(operation["security"], [{"api_key": []}])

    def test_public_method(self):
        operation = self._get_operation(self._get_spec("public"), "public")
        self.assertNotIn("security", operation)

    def test_default_auth_api_key(self):
        spec = self._get_spec("api_key")
        operation = self._get_operation(spec, "public_or_default")
        self.assertEqual(operation["security"], [{"api_key": []}])
