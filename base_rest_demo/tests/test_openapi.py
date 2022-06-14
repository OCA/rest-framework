# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import jsondiff

from .common import CommonCase, get_canonical_json


class TestOpenAPI(CommonCase):
    def _fix_server_url(self, openapi_def):
        # The server url depends of base_url. base_url depends of the odoo
        # config
        url = openapi_def["servers"][0]["url"]
        url.replace("http://localhost:8069", self.base_url)
        openapi_def["servers"][0]["url"] = url

    def _fix_openapi_components(self, openapi_def):
        """
        Remove additional components that could be added by others addons than
        base_rest
        """
        security_components = openapi_def.get("components", {}).get(
            "securitySchemes", {}
        )
        unknow_keys = set(security_components.keys()) - {"user"}
        for key in unknow_keys:
            del security_components[key]

    def assertOpenApiDef(self, service, canocincal_json_file, default_auth):
        openapi_def = service.to_openapi(default_auth=default_auth)
        self._fix_openapi_components(openapi_def)
        canonical_def = get_canonical_json(canocincal_json_file)
        self._fix_server_url(canonical_def)
        self.assertFalse(jsondiff.diff(openapi_def, canonical_def))

    def test_partner_api(self):
        service = self.private_services_env.component(usage="partner")
        self.assertOpenApiDef(service, "partner_api.json", "user")

    def test_ping_api(self):
        service = self.public_services_env.component(usage="ping")
        self.assertOpenApiDef(service, "ping_api.json", "public")

    def test_partner_image_api(self):
        service = self.private_services_env.component(usage="partner_image")
        self.assertOpenApiDef(service, "partner_image_api.json", "user")

    def test_partner_pydantic_api(self):
        service = self.new_api_services_env.component(usage="partner_pydantic")
        self.assertOpenApiDef(service, "partner_pydantic_api.json", "public")
