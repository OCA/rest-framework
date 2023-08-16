import json
from contextlib import contextmanager
from functools import partial

from fastapi import status
from requests import Response

from odoo.tests.common import tagged

from odoo.addons.extendable_fastapi.tests.common import FastAPITransactionCase
from odoo.addons.fastapi.dependencies import fastapi_endpoint

from ..routers.authenticable import auth_router


@tagged("post_install", "-at_install")
class TestAuth(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, test_queue_job_no_delay=True))
        cls.default_fastapi_router = auth_router

    @contextmanager
    def _create_test_auth_client(self):
        demo_app = self.env.ref("partner_auth.fastapi_endpoint_demo")
        with self._create_test_client(
            demo_app._get_app(),
            dependency_overrides={fastapi_endpoint: partial(lambda a: a, demo_app)},
            env=self.env,
        ) as test_client:
            yield test_client

    def _register_partner(self):
        with self._create_test_auth_client() as test_client:
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
        return response

    def test_register(self):
        response = self._register_partner()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json(), {"login": "loriot@example.org"})

    def test_login(self):
        self._register_partner()
        with self._create_test_auth_client() as test_client:
            response: Response = test_client.post(
                "/auth/login",
                content=json.dumps(
                    {
                        "login": "loriot@example.org",
                        "password": "supersecret",
                    }
                ),
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), {"login": "loriot@example.org"})

    def test_logout(self):
        self._register_partner()
        with self._create_test_auth_client() as test_client:
            response: Response = test_client.post("/auth/logout")
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

    def test_forget_password(self):
        self._register_partner()
        with self._create_test_auth_client() as test_client:
            response: Response = test_client.post(
                "/auth/forget_password",
                content=json.dumps({"login": "loriot@example.org"}),
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            response: Response = test_client.post(
                "/auth/set_password",
                content=json.dumps(
                    {
                        "login": "loriot@example.org",
                        "token": "TODO",
                    }
                ),
            )
