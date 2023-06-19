# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import os
import unittest

from odoo.tests.common import HttpCase


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class FastAPIHttpCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fastapi_demo_app = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.fastapi_demo_app._handle_registry_sync()
        lang = (
            cls.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "=", "fr_BE")])
        )
        lang.active = True

    def _assert_expected_lang(self, accept_language, expected_lang):
        route = "/fastapi_demo/demo/lang"
        response = self.url_open(route, headers={"Accept-language": accept_language})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected_lang)

    def test_call(self):
        route = "/fastapi_demo/demo/"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"Hello":"World"}')

    def test_lang(self):
        self._assert_expected_lang("fr,en;q=0.7,en-GB;q=0.3", b'"fr_BE"')
        self._assert_expected_lang("en,fr;q=0.7,en-GB;q=0.3", b'"en_US"')
        self._assert_expected_lang("fr-FR,en;q=0.7,en-GB;q=0.3", b'"fr_BE"')
        self._assert_expected_lang("fr-FR;q=0.1,en;q=1.0,en-GB;q=0.8", b'"en_US"')
