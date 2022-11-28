# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
from urllib.parse import quote

import odoo.tools
from odoo.tests import HttpCase
from odoo.tests.common import tagged

from odoo.addons.base_rest.tests.common import RegistryMixin


@tagged("-at_install", "post_install")
class TestService(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.setUpRegistry()
        host = "127.0.0.1"
        port = odoo.tools.config["http_port"]
        cls.url = "http://%s:%d/base_rest_demo_api/new_api/partner" % (host, port)
        cls.partner = cls.env.ref("base.partner_demo")
        # Define a subset of the partner values to check against returned payload
        cls.expected_partner_values = {
            "country": {
                "id": cls.partner.country_id.id,
                "name": cls.partner.country_id.name,
            },
            "id": cls.partner.id,
            "name": cls.partner.name,
            "state": {"id": cls.partner.state_id.id, "name": cls.partner.state_id.name},
        }

    def test_get(self):
        """Test a new api GET method"""
        self.authenticate("admin", "admin")
        self.opener.headers["Content-Type"] = "application/json"
        response = self.url_open(
            "%s/%s" % (self.url, self.partner.id),
            headers={"Accept-language": "en-US,en;q=0.5"},
        )
        body = json.loads(response.content.decode("utf-8"))
        self.assertEqual(body, body | self.expected_partner_values)

    def test_get_by_name(self):
        """Test a new api GET method with string argument"""
        self.authenticate("admin", "admin")
        self.opener.headers["Content-Type"] = "application/json"
        response = self.url_open(
            "%s/%s" % (self.url, quote(self.partner.name)),
            headers={"Accept-language": "en-US,en;q=0.5"},
        )
        body = json.loads(response.content.decode("utf-8"))
        self.assertEqual(body, body | self.expected_partner_values)
