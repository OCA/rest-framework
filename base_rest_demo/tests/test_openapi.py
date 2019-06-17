# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import jsondiff

from .common import CommonCase, get_canonical_json


class TestOpenAPI(CommonCase):

    def _fix_server_url(self, openapi_def):
        # The server url depends of base_url. base_url depends of the odoo
        # config
        url = openapi_def['servers'][0]['url']
        url.replace('http://localhost:8069', self.base_url)
        openapi_def['servers'][0]['url'] = url

    def test_partner_api(self):
        partner_service = self.private_services_env.component(
            usage="partner")
        openapi_def = partner_service.to_openapi()
        canonical_def = get_canonical_json("partner_api.json")
        self._fix_server_url(canonical_def)
        self.assertFalse(
            jsondiff.diff(openapi_def, canonical_def))

    def test_ping_api(self):
        ping_service = self.public_services_env.component(
            usage="ping"
        )
        openapi_def = ping_service.to_openapi()
        canonical_def = get_canonical_json("ping_api.json")
        self._fix_server_url(canonical_def)
        self.assertFalse(
            jsondiff.diff(openapi_def, canonical_def))

    def test_partner_image_api(self):
        partner_service = self.private_services_env.component(
            usage="partner_image")
        openapi_def = partner_service.to_openapi()
        canonical_def = get_canonical_json("partner_image_api.json")
        self._fix_server_url(canonical_def)
        self.assertFalse(
            jsondiff.diff(openapi_def, canonical_def))
