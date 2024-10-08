# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
from contextlib import contextmanager
from functools import partial

from requests import Response

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.auth_partner.tests.common import CommonTestAuthPartner
from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase
from odoo.addons.fastapi.dependencies import fastapi_endpoint

from fastapi import status

from ..routers.auth import auth_router


class CommonTestAuth(FastAPITransactionCase):
    @contextmanager
    def _create_test_client(self, **kwargs):
        self.env.invalidate_all()
        with mute_logger("httpx"):
            with super()._create_test_client(**kwargs) as test_client:
                yield test_client

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.demo_app = cls.env.ref("fastapi_auth_partner.fastapi_endpoint_demo")
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))
        cls.default_fastapi_router = auth_router
        cls.default_fastapi_app = cls.demo_app._get_app()
        cls.default_fastapi_dependency_overrides = {
            fastapi_endpoint: partial(lambda a: a, cls.demo_app)
        }
        cls.default_fastapi_odoo_env = cls.env
        cls.default_fastapi_running_user = cls.demo_app.user_id

    def _register_partner(self):
        with self._create_test_client() as test_client, self.new_mails() as new_mails:
            response: Response = test_client.post(
                "/auth/register",
                content=json.dumps(
                    {
                        "name": "Loriot",
                        "login": "loriot@example.org",
                        "password": "supersecret",
                    }
                ),
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.text)
        return response, new_mails

    def _login(self, test_client, password="supersecret"):
        response: Response = test_client.post(
            "/auth/login",
            content=json.dumps(
                {
                    "login": "loriot@example.org",
                    "password": password,
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        return response


@tagged("post_install", "-at_install")
class TestFastapiAuthPartner(CommonTestAuth, CommonTestAuthPartner):
    def test_register(self):
        response, new_mails = self._register_partner()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.text)
        self.assertEqual(
            response.json(), {"login": "loriot@example.org", "mail_verified": False}
        )
        self.assertEqual(len(new_mails), 1)
        self.assertIn(
            "please click on the following link to verify your email",
            str(new_mails.body),
        )

    def test_login(self):
        self._register_partner()
        with self._create_test_client() as test_client:
            response = self._login(test_client)
        self.assertEqual(
            response.json(), {"login": "loriot@example.org", "mail_verified": False}
        )

    def test_logout(self):
        self._register_partner()
        with self._create_test_client() as test_client:
            response: Response = test_client.post("/auth/logout")
        self.assertEqual(
            response.status_code, status.HTTP_205_RESET_CONTENT, response.text
        )

    def test_request_reset_password(self):
        self._register_partner()
        with self._create_test_client() as test_client, self.new_mails() as new_mails:
            response: Response = test_client.post(
                "/auth/request_reset_password",
                content=json.dumps({"login": "loriot@example.org"}),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
            self.assertFalse(
                self.env["auth.partner"]
                .search([("login", "=", "loriot@example.org")])
                .mail_verified,
            )
            self.assertEqual(len(new_mails), 1)
            self.assertIn(
                "Click on the following link to reset your password",
                str(new_mails.body),
            )
            token = str(new_mails.body).split("token=")[1].split('">')[0]
            response: Response = test_client.post(
                "/auth/set_password",
                content=json.dumps(
                    {
                        "password": "megasecret",
                        "token": token,
                    }
                ),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)

            self.assertTrue(
                self.env["auth.partner"]
                .search([("login", "=", "loriot@example.org")])
                .mail_verified,
            )
            response = self._login(test_client, password="megasecret")
            self.assertEqual(
                response.json(), {"login": "loriot@example.org", "mail_verified": True}
            )

    def test_validate_email(self):
        self._register_partner()
        mail = self.env["mail.mail"].search([], limit=1, order="id desc")
        self.assertIn(
            "please click on the following link to verify your email", str(mail.body)
        )
        self.assertFalse(
            self.env["auth.partner"]
            .search([("login", "=", "loriot@example.org")])
            .mail_verified,
        )
        token = str(mail.body).split("token=")[1].split('">')[0]
        with self._create_test_client() as test_client:
            response: Response = test_client.post(
                "/auth/validate_email",
                content=json.dumps({"token": token}),
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)

        self.assertTrue(
            self.env["auth.partner"]
            .search([("login", "=", "loriot@example.org")])
            .mail_verified,
        )

    def test_impersonate(self):
        self.demo_app.public_url = self.demo_app.public_api_url = False
        self._register_partner()
        auth_partner = self.env["auth.partner"].search(
            [("login", "=", "loriot@example.org")]
        )
        self.assertEqual(len(auth_partner), 1)
        action = auth_partner.with_user(self.env.ref("base.user_admin")).impersonate()
        url = action["url"].split("fastapi_auth_partner_demo", 1)[1]

        with self._create_test_client() as test_client:
            response: Response = test_client.get(url, follow_redirects=False)
        self.assertEqual(response.status_code, status.HTTP_307_TEMPORARY_REDIRECT)
        self.assertTrue(
            response.headers["location"].endswith("/fastapi_auth_partner_demo")
        )
        self.assertIn("fastapi_auth_partner", response.cookies)

    def test_impersonate_api_url(self):
        self._register_partner()
        auth_partner = self.env["auth.partner"].search(
            [("login", "=", "loriot@example.org")]
        )
        self.assertEqual(len(auth_partner), 1)
        action = auth_partner.with_user(self.env.ref("base.user_admin")).impersonate()
        self.assertTrue(
            action["url"].startswith("https://api.example.com/auth/impersonate/")
        )
        action["url"].split("auth/impersonate/", 1)[1]

    def test_wizard_auth_partner_impersonate(self):
        self._register_partner()
        action = (
            self.env["wizard.auth.partner.impersonate"]
            .create(
                {
                    "auth_partner_id": self.env["auth.partner"]
                    .search([("login", "=", "loriot@example.org")])
                    .id,
                    "fastapi_endpoint_id": self.demo_app.id,
                }
            )
            .with_user(self.env.ref("base.user_admin"))
            .action_impersonate()
        )
        self.assertTrue(
            action["url"].startswith("https://api.example.com/auth/impersonate/")
        )

    def test_wizard_auth_partner_reset_password(self):
        self._register_partner()

        template = self.env.ref("auth_partner.email_reset_password")
        template.body_html = template.body_html.replace(
            "https://example.org/", "{{ object.env.context['public_url'] }}"
        )
        with self.new_mails() as new_mails:
            self.env["wizard.auth.partner.reset.password"].create(
                {
                    "delay": "2-days",
                    "template_id": template.id,
                    "fastapi_endpoint_id": self.demo_app.id,
                }
            ).with_context(
                active_ids=self.env["auth.partner"]
                .search([("login", "=", "loriot@example.org")])
                .ids
            ).action_reset_password()

        self.assertEqual(len(new_mails), 1)
        self.assertIn(
            "Click on the following link to reset your password", str(new_mails.body)
        )
        self.assertIn(
            "https://www.example.com/password/reset?token=", str(new_mails.body)
        )
