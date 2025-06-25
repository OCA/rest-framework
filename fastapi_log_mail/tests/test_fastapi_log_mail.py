# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import unittest

from odoo.addons.fastapi.schemas import DemoExceptionType
from odoo.addons.fastapi_log.tests.common import Common
from odoo.addons.mail.tests.common import MailCase

from fastapi import status


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "TestFastapiLogMail skipped")
class TestFastapiLogMail(Common, MailCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fastapi_demo_app.api_log_mail_exception_activity_type_id = cls.env[
            "mail.activity.type"
        ].create(
            {
                "name": "Test exception activity type",
                "res_model": "api.log",
            }
        )
        cls.fastapi_demo_app.api_log_mail_exception_template_id = cls.env[
            "mail.template"
        ].create(
            {
                "name": "Test exception email template",
                "model_id": cls.env.ref("api_log.model_api_log").id,
            }
        )

    def test_endpoint_exception_create_activity(self):
        """If an endpoint has an activity type,
        when an exception occurs an activity of the configured type is created.
        """
        # Arrange
        app = self.fastapi_demo_app
        activity_type = app.api_log_mail_exception_activity_type_id
        route = (
            "/fastapi_demo/test/demo/exception?"
            f"exception_type={DemoExceptionType.user_error.value}"
            "&error_message=An error happened"
        )
        # pre-condition
        self.assertTrue(activity_type)

        # Act
        with self.log_capturer() as capturer:
            response = self.url_open(route, timeout=200)

        # Assert
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        log = capturer.records
        self.assertEqual(len(log), 1)
        self.assertTrue(log.activity_ids)

    def test_endpoint_exception_send_email(self):
        """If an endpoint has an email template,
        when an exception occurs an email is sent using the configured template.
        """
        # Arrange
        app = self.fastapi_demo_app
        mail_template = app.api_log_mail_exception_template_id
        route = (
            "/fastapi_demo/test/demo/exception?"
            f"exception_type={DemoExceptionType.user_error.value}"
            "&error_message=An error happened"
        )
        # pre-condition
        self.assertTrue(mail_template)

        # Act
        with self.mock_mail_gateway():
            self.url_open(route, timeout=200)

        # Assert
        sent_email = self._filter_mail()
        self.assertTrue(sent_email)
