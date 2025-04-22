# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import unittest

from odoo.addons.api_log.tests.common import CommonAPILog
from odoo.addons.fastapi.schemas import DemoExceptionType
from odoo.addons.mail.tests.common import MailCase


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "FastAPIEncryptedErrorsCase skipped")
class FastAPIEncryptedErrorsCase(CommonAPILog, MailCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fastapi_demo_app = cls.env.ref("fastapi.fastapi_endpoint_demo")

        cls.fastapi_demo_app._handle_registry_sync()
        cls.fastapi_demo_app.log_requests = True
        cls.fastapi_demo_app.fastapi_log_mail_template_id = cls.env[
            "mail.template"
        ].create(
            {
                "name": "Test exception email template",
                "model_id": cls.env.ref("api_log.model_api_log").id,
            }
        )

    def test_endpoint_exception_send_email(self):
        """If an endpoint has an email template,
        when an exception occurs an email is sent using the configured template.
        """
        # Arrange
        mail_template = self.fastapi_demo_app.fastapi_log_mail_template_id
        route = (
            "/fastapi_demo/demo/exception?"
            f"exception_type={DemoExceptionType.user_error.value}"
            "&error_message=User Error"
        )
        # pre-condition
        self.assertTrue(mail_template)

        # Act
        with self.mock_mail_gateway():
            self.url_open(route, timeout=200)

        # Assert
        sent_email = self._filter_mail()
        self.assertTrue(sent_email)
