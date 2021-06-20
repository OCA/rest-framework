# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import odoo.tests.common
from odoo.tests import new_test_user
from odoo.tests.common import HttpCase

HOST = "127.0.0.1"
PORT = odoo.tools.config["http_port"]


@odoo.tests.common.at_install(False)
@odoo.tests.common.post_install(True)
class TestPartnerNewAPI(HttpCase):
    def setUp(self):
        super().setUp()
        self.partner_data = {
            "name": "Test Partner",
            "country_id": self.env["res.country"].search([], limit=1).id,
            "state_id": self.env["res.country.state"].search([], limit=1).id,
        }
        self.test_partner = self.env["res.partner"].create(self.partner_data)
        self.password = "test_password"
        self.user = new_test_user(
            self.env,
            login="test_user",
            password=self.password,
            groups="base.group_user",
        )

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_01(self):
        """Test GET"""
        self.authenticate("admin", "admin")
        # self.authenticate(self.user.login, self.password)
        url = "http://{}:{}/base_rest_demo_api/new_api/partner/{}".format(
            HOST, PORT, self.test_partner.id
        )
        response = self.opener.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        data = response.json()
        self.assertEqual(data["name"], self.partner_data["name"])
        self.assertEqual(data["country"]["id"], self.partner_data["country_id"])
        self.assertEqual(data["state"]["id"], self.partner_data["state_id"])
