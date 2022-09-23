# Copyright 2021 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import os
import unittest

from odoo.tests.common import HttpCase


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class FastAPIHttpCase(HttpCase):
    def setUp(self):
        super().setUp()
        self.fastapi_demo_app = self.env.ref("fastapi.fastapi_app_demo")

    def test_call(self):
        route = "/fastapi_demo/"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"Hello":"World"}')

    def test_update_route(self):
        route = "/fastapi_demo/"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        response = self.url_open("/new_root/")
        self.assertEqual(response.status_code, 404)
        self.fastapi_demo_app.root_path = "/new_root"
        self.env.flush_all()
        response = self.url_open(route)
        self.assertEqual(response.status_code, 404)
        response = self.url_open("/new_root/")
        self.assertEqual(response.status_code, 200)

    def test_odoo_env_depends(self):
        route = "/fastapi_demo/contacts"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        count = self.env["res.partner"].sudo().search_count([])
        expected = b'{"count":%d}' % count
        self.assertEqual(response.content, expected)
