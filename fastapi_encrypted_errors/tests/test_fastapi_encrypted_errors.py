# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import unittest

from odoo.tests.common import HttpCase

from odoo.addons.fastapi.schemas import DemoExceptionType

from fastapi import status


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "FastAPIEncryptedErrorsCase skipped")
class FastAPIEncryptedErrorsCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fastapi_demo_app = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.fastapi_demo_app._handle_registry_sync()
        cls.fastapi_demo_app.write({"encrypt_errors": True})
        lang = (
            cls.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "=", "fr_BE")])
        )
        lang.active = True

    def test_encrypted_errors_in_response(self):
        route = (
            "/fastapi_demo/demo/exception?"
            f"exception_type={DemoExceptionType.user_error.value}"
            "&error_message=User Error"
        )
        response = self.url_open(route, timeout=200)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        res = response.json()
        self.assertEqual(res["detail"], "User Error")
        self.assertIn("ref", res)

        route = (
            "/fastapi_demo/demo/exception?"
            f"exception_type={DemoExceptionType.bare_exception.value}"
            "&error_message=Internal Server Error"
        )
        response = self.url_open(route, timeout=200)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res = response.json()
        self.assertEqual(res["detail"], "Internal Server Error")
        self.assertIn("ref", res)

    def test_encrypted_errors_decrypt(self):
        route = (
            "/fastapi_demo/demo/exception?"
            f"exception_type={DemoExceptionType.bare_exception.value}"
            "&error_message=Internal Server Error"
        )
        response = self.url_open(route, timeout=200)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        res = response.json()
        self.assertEqual(res["detail"], "Internal Server Error")
        self.assertIn("ref", res)
        ref = res["ref"]
        self.assertNotIn("Traceback (most recent call last)", ref)
        self.assertNotIn("NotImplementedError: Internal Server Error", ref)

        wizard = self.env["wizard.fastapi.decrypt.errors"].create({"error": ref})
        wizard.action_decrypt_error()
        self.assertIn("Traceback (most recent call last)", wizard.decrypted_error)
        self.assertIn(
            "NotImplementedError: Internal Server Error", wizard.decrypted_error
        )
