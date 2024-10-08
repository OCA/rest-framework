import json
from contextlib import contextmanager
from functools import partial

from requests import Response

from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase
from odoo.addons.fastapi.dependencies import fastapi_endpoint

from fastapi import status

from ..routers.auth import auth_router


class CommonTestAuth(FastAPITransactionCase):
    @contextmanager
    def _create_test_client(self, **kwargs):
        with mute_logger("httpx"):
            with super()._create_test_client(**kwargs) as test_client:
                yield test_client

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.demo_app = cls.env.ref("fastapi_auth_partner.fastapi_endpoint_demo")
        cls.env = cls.env(context=dict(cls.env.context, test_queue_job_no_delay=True))
        cls.default_fastapi_router = auth_router
        cls.default_fastapi_app = cls.demo_app._get_app()
        cls.default_fastapi_dependency_overrides = {
            fastapi_endpoint: partial(lambda a: a, cls.demo_app)
        }
        cls.default_fastapi_odoo_env = cls.env

    def _register_partner(self):
        with self._create_test_client() as test_client:
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
        return response

    def _login(self, test_client):
        response: Response = test_client.post(
            "/auth/login",
            content=json.dumps(
                {
                    "login": "loriot@example.org",
                    "password": "supersecret",
                }
            ),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
        return response


@tagged("post_install", "-at_install")
class TestAuth(CommonTestAuth):
    def test_register(self):
        response = self._register_partner()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.text)
        self.assertEqual(
            response.json(), {"login": "loriot@example.org", "mail_verified": False}
        )
        mail = self.env["mail.mail"].search([], limit=1, order="id desc")
        self.assertIn(
            "please click on the following link to verify your email", str(mail.body)
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
        with self._create_test_client() as test_client:
            response: Response = test_client.post(
                "/auth/request_reset_password",
                content=json.dumps({"login": "loriot@example.org"}),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
            self.assertFalse(
                self.env["fastapi.auth.partner"]
                .search([("login", "=", "loriot@example.org")])
                .mail_verified,
            )
            mail = self.env["mail.mail"].search([], limit=1, order="id desc")
            self.assertIn(
                "Click on the following link to reset your password", str(mail.body)
            )
            token = str(mail.body).split("token=")[1].split('">')[0]
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
                self.env["fastapi.auth.partner"]
                .search([("login", "=", "loriot@example.org")])
                .mail_verified,
            )

    def test_validate_email(self):
        self._register_partner()
        mail = self.env["mail.mail"].search([], limit=1, order="id desc")
        self.assertIn(
            "please click on the following link to verify your email", str(mail.body)
        )
        self.assertFalse(
            self.env["fastapi.auth.partner"]
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
            self.env["fastapi.auth.partner"]
            .search([("login", "=", "loriot@example.org")])
            .mail_verified,
        )
