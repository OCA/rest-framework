# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import os
import unittest

from odoo.tests.common import HttpCase


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class FastAPIHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.fastapi_demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
        self.fastapi_demo_app._handle_registry_sync()

    def test_call(self):
        route = "/fastapi_demo/"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"Hello":"World"}')
