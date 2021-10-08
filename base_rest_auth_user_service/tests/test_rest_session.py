# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import odoo.tests.common
from odoo.http import root
from odoo.tests import new_test_user
from odoo.tests.common import HttpCase

HOST = "127.0.0.1"
PORT = odoo.tools.config["http_port"]


@odoo.tests.tagged("post_install", "-at_install")
class TestSessionRestAPI(HttpCase):
    def setUp(self):
        super().setUp()
        self.password = "test_password"
        self.user = new_test_user(self.env, login="test_user", password=self.password)

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_01(self):
        """Test authentication"""
        params = {
            "db": self.env.cr.dbname,
            "login": self.user.login,
            "password": self.password,
        }
        url = "http://{}:{}{}".format(HOST, PORT, "/session/auth/login")
        response = self.opener.post(url, json=params)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        data = response.json()
        session = root.session_store.get(data["session"]["sid"])
        self.assertEqual(session.login, self.user.login)

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_02(self):
        """Test logout"""
        self.authenticate(self.user.login, self.password)
        self.assertEqual(self.session.login, self.user.login)
        url = "http://{}:{}{}".format(HOST, PORT, "/session/auth/logout")
        response = self.opener.post(
            url, headers={"X-Openerp-Session-Id": self.session.sid}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        session = root.session_store.get(self.session.sid)
        self.assertIsNone(session.login)
