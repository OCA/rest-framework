# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json

import odoo.tools
from odoo.tests import HttpCase
from odoo.tests.common import tagged

from odoo.addons.base_rest.tests.common import RegistryMixin


@tagged("-at_install", "post_install")
class TestException(HttpCase, RegistryMixin):
    @classmethod
    def setUpClass(cls):
        super(TestException, cls).setUpClass()
        cls.setUpRegistry()
        host = "127.0.0.1"
        port = odoo.tools.config["http_port"]
        cls.url = "http://%s:%d/base_rest_demo_api/public/exception" % (host, port)

    def setUp(self):
        super(TestException, self).setUp()
        self.opener.headers["Content-Type"] = "application/json"

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_user_error(self):
        response = self.url_open("%s/user_error" % self.url, "{}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(
            body,
            {
                "code": 400,
                "name": "Bad Request",
                "description": "<p>UserError message</p>",
            },
        )

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_validation_error(self):
        response = self.url_open("%s/validation_error" % self.url, "{}")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(
            body,
            {
                "code": 400,
                "name": "Bad Request",
                "description": "<p>ValidationError message</p>",
            },
        )

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_session_expired(self):
        response = self.url_open("%s/session_expired" % self.url, "{}")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(body, {"code": 401, "name": "Unauthorized"})

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_missing_error(self):
        response = self.url_open("%s/missing_error" % self.url, "{}")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(body, {"code": 404, "name": "Not Found"})

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_access_error(self):
        response = self.url_open("%s/access_error" % self.url, "{}")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(body, {"code": 403, "name": "Forbidden"})

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_access_denied(self):
        response = self.url_open("%s/access_denied" % self.url, "{}")
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(body, {"code": 403, "name": "Forbidden"})

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_http_exception(self):
        response = self.url_open("%s/http_exception" % self.url, "{}")
        self.assertEqual(response.status_code, 405)
        self.assertEqual(response.headers["content-type"], "text/html")
        body = response.content
        self.assertIn(b"Method Not Allowed", body)

    @odoo.tools.mute_logger("odoo.addons.base_rest.http")
    def test_bare_exception(self):
        response = self.url_open("%s/bare_exception" % self.url, "{}")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.headers["content-type"], "application/json")
        body = json.loads(response.content.decode("utf-8"))
        self.assertDictEqual(body, {"code": 500, "name": "Internal Server Error"})
