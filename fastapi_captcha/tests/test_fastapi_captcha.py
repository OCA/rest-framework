# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from unittest.mock import patch

import requests

from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from fastapi import status


class FastAPICaptcha(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_fastapi_running_user = cls.env.ref("fastapi.my_demo_app_user")
        cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
            {"name": "FastAPI Demo"}
        )
        cls.endpoint = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.endpoint.use_captcha = True
        cls.endpoint.captcha_type = "recaptcha"
        cls.endpoint.captcha_secret_key = "test_secret"
        cls.default_fastapi_app = cls.endpoint._get_app()

    def test_no_secret_key(self):
        self.endpoint.captcha_secret_key = False
        with self._create_test_client() as test_client:
            with self.assertRaisesRegex(
                UserError,
                "No secret key found for this endpoint",
            ):
                test_client.get("/demo/", headers={"X-Captcha-Token": "valid"})

    def test_invalid_regex(self):
        with self.assertRaisesRegex(
            ValidationError,
            r"Invalid regex for captcha routes: /route/\( ",
        ):
            self.endpoint.captcha_routes_regex = r"/route/("

    def test_missing_header(self):
        with self._create_test_client() as test_client:
            with self.assertRaisesRegex(
                AccessError,
                "Captcha token not found in headers",
            ):
                test_client.get("/demo/")
            with self.assertRaisesRegex(
                AccessError,
                "Captcha token not found in headers",
            ):
                test_client.get("/demo/who_ami")

    def test_invalid_header_recaptcha(self):
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "success": False,
                "error-codes": ["invalid-input-response"],
            }
            with self._create_test_client() as test_client:
                with self.assertRaisesRegex(
                    AccessError,
                    "Recaptcha validation failed: invalid-input-response",
                ):
                    test_client.get("/demo/", headers={"X-Captcha-Token": "invalid"})
                with self.assertRaisesRegex(
                    AccessError,
                    "Recaptcha validation failed: invalid-input-response",
                ):
                    test_client.get(
                        "/demo/who_ami", headers={"X-Captcha-Token": "invalid"}
                    )

    def test_valid_header_recaptcha(self):
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "success": True,
                "score": 0.9,
            }
            with self._create_test_client() as test_client:
                response = test_client.get(
                    "/demo/", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json(), {"Hello": "World"})

                response = test_client.get(
                    "/demo/who_ami", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                partner = self.default_fastapi_authenticated_partner
                self.assertDictEqual(
                    response.json(),
                    {
                        "name": partner.name,
                        "display_name": partner.display_name,
                    },
                )

    def test_invalid_header_hcaptcha(self):
        self.endpoint.captcha_type = "hcaptcha"
        self.endpoint.captcha_minimum_score = 0.8
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "success": False,
                "error-codes": ["invalid-input-response"],
            }
            with self._create_test_client() as test_client:
                with self.assertRaisesRegex(
                    AccessError,
                    "Hcaptcha validation failed: invalid-input-response",
                ):
                    test_client.get("/demo/", headers={"X-Captcha-Token": "invalid"})
                with self.assertRaisesRegex(
                    AccessError,
                    "Hcaptcha validation failed: invalid-input-response",
                ):
                    test_client.get(
                        "/demo/who_ami", headers={"X-Captcha-Token": "invalid"}
                    )

    def test_valid_header_hcaptcha(self):
        self.endpoint.captcha_type = "hcaptcha"
        self.endpoint.captcha_minimum_score = 0.8
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "success": True,
                "score": 0.9,
            }
            with self._create_test_client() as test_client:
                response = test_client.get(
                    "/demo/", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json(), {"Hello": "World"})

                response = test_client.get(
                    "/demo/who_ami", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                partner = self.default_fastapi_authenticated_partner
                self.assertDictEqual(
                    response.json(),
                    {
                        "name": partner.name,
                        "display_name": partner.display_name,
                    },
                )

    def test_valid_header_low_score_hcaptcha(self):
        self.endpoint.captcha_type = "hcaptcha"
        self.endpoint.captcha_minimum_score = 0.8
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "success": True,
                "score": 0.6,
                "score_reason": "low-confidence",
            }
            with self._create_test_client() as test_client:
                with self.assertRaisesRegex(
                    AccessError,
                    r"Hcaptcha validation failed: score 0.6 < 0.8 \(low-confidence\)",
                ):
                    test_client.get("/demo/", headers={"X-Captcha-Token": "valid"})

    def test_invalid_header_altcha(self):
        self.endpoint.captcha_type = "altcha"
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "verified": False,
                "error": "invalid-input-response",
            }
            with self._create_test_client() as test_client:
                with self.assertRaisesRegex(
                    AccessError,
                    r"Altcha \(https://eu.altcha.org/api/v1/challenge/verify\) "
                    "validation failed: invalid-input-response",
                ):
                    test_client.get("/demo/", headers={"X-Captcha-Token": "invalid"})

                self.assertGreaterEqual(mock_post.call_count, 1)
                self.assertEqual(
                    mock_post.call_args.args[0],
                    "https://eu.altcha.org/api/v1/challenge/verify",
                )

                with self.assertRaisesRegex(
                    AccessError,
                    r"Altcha \(https://eu.altcha.org/api/v1/challenge/verify\) "
                    "validation failed: invalid-input-response",
                ):
                    test_client.get(
                        "/demo/who_ami", headers={"X-Captcha-Token": "invalid"}
                    )

    def test_valid_header_altcha(self):
        self.endpoint.captcha_type = "altcha"
        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "verified": True,
            }
            with self._create_test_client() as test_client:
                response = test_client.get(
                    "/demo/", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json(), {"Hello": "World"})

                self.assertGreaterEqual(mock_post.call_count, 1)
                self.assertEqual(
                    mock_post.call_args.args[0],
                    "https://eu.altcha.org/api/v1/challenge/verify",
                )
                response = test_client.get(
                    "/demo/who_ami", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                partner = self.default_fastapi_authenticated_partner
                self.assertDictEqual(
                    response.json(),
                    {
                        "name": partner.name,
                        "display_name": partner.display_name,
                    },
                )

    def test_valid_header_custom_url_altcha(self):
        self.endpoint.captcha_type = "altcha"
        self.endpoint.captcha_custom_verify_url = "https://custom.exemple.org/verify"

        with patch(
            "odoo.addons.fastapi_captcha.models.fastapi_endpoint.requests.post",
            return_value=requests.Response(),
        ) as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json = lambda: {
                "verified": True,
            }
            with self._create_test_client() as test_client:
                response = test_client.get(
                    "/demo/", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.json(), {"Hello": "World"})

                self.assertGreaterEqual(mock_post.call_count, 1)
                self.assertEqual(
                    mock_post.call_args.args[0],
                    "https://custom.exemple.org/verify",
                )
                response = test_client.get(
                    "/demo/who_ami", headers={"X-Captcha-Token": "valid"}
                )
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                partner = self.default_fastapi_authenticated_partner
                self.assertDictEqual(
                    response.json(),
                    {
                        "name": partner.name,
                        "display_name": partner.display_name,
                    },
                )

    def test_routes_matching_1(self):
        self.endpoint.captcha_routes_regex = "/demo/wh.*,/demo/ca.?"
        # Refresh app
        self.default_fastapi_app = self.endpoint._get_app()

        with self._create_test_client() as test_client:
            response = test_client.get("/demo")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), {"Hello": "World"})

            with self.assertRaisesRegex(
                AccessError,
                "Captcha token not found in headers",
            ):
                test_client.get("/demo/who_ami")

    def test_routes_matching_2(self):
        self.endpoint.captcha_routes_regex = "/demo"
        # Refresh app
        self.default_fastapi_app = self.endpoint._get_app()

        with self._create_test_client() as test_client:
            with self.assertRaisesRegex(
                AccessError,
                "Captcha token not found in headers",
            ):
                test_client.get("/demo")

            response = test_client.get("/demo/who_ami")
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            partner = self.default_fastapi_authenticated_partner
            self.assertDictEqual(
                response.json(),
                {
                    "name": partner.name,
                    "display_name": partner.display_name,
                },
            )
