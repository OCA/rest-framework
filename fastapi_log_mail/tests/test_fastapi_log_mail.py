# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import os
import unittest

from odoo.tools import mute_logger

from odoo.addons.fastapi.schemas import DemoExceptionType
from odoo.addons.fastapi_log.tests.common import Common
from odoo.addons.mail.tests.common import MailCase

from fastapi import status


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "TestFastapiLogMail skipped")
class TestFastapiLogMail(Common, MailCase):
    def _set_mail_exception_activity_type(self, app):
        app.api_log_mail_exception_activity_type_id = app.env[
            "mail.activity.type"
        ].create(
            {
                "name": "Test exception activity type",
                "res_model": "api.log",
            }
        )

    def _set_mail_exception_template(self, app):
        app.api_log_mail_exception_template_id = app.env["mail.template"].create(
            {
                "name": "Test exception email template",
                "model_id": app.env.ref("api_log.model_api_log").id,
            }
        )

    @mute_logger("odoo.http", "odoo.addons.base.models.assetsbundle")
    def test_endpoint_exception_create_activity(self):
        """If an endpoint has an activity type,
        when an exception occurs an activity of the configured type is created.
        """
        # Arrange
        app = self._get_log_env_records(self.fastapi_demo_app)
        self._set_mail_exception_activity_type(app)
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

    @mute_logger("odoo.http", "odoo.addons.base.models.assetsbundle")
    def test_endpoint_exception_send_email(self):
        """If an endpoint has an email template,
        when an exception occurs an email is sent using the configured template.
        """
        # Arrange
        app = self._get_log_env_records(self.fastapi_demo_app)
        self._set_mail_exception_template(app)
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
