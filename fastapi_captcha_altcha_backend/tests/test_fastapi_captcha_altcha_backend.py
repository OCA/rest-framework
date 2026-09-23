# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import json

from altcha import Challenge, Payload, solve_challenge, solve_challenge_v1

from odoo.exceptions import AccessError

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from fastapi import status

from ..routers import altcha_router


class FastAPICaptchaAltchaBackend(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.default_fastapi_running_user = cls.env.ref("fastapi.my_demo_app_user")
        cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
            {"name": "FastAPI Demo"}
        )
        cls.endpoint = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.endpoint.use_captcha = True
        cls.endpoint.captcha_type = "altcha_local"
        cls.endpoint.captcha_secret_key = "test_secret"
        cls.endpoint.captcha_routes_regex = "/demo"
        cls.default_fastapi_app = cls.endpoint._get_app()
        cls.default_fastapi_app.include_router(altcha_router)
        cls.default_fastapi_dependency_overrides = {
            k: v
            for k, v in cls.default_fastapi_app.dependency_overrides.items()
            if k.__name__ != "authenticated_partner_impl"
        }

    def test_missing_header(self):
        with self._create_test_client() as test_client:
            with self.assertRaisesRegex(
                AccessError,
                "Captcha token not found in headers",
            ):
                test_client.get("/demo/")

    def test_valid_header_altcha_v1(self):
        with self._create_test_client() as test_client:
            response = test_client.get("/altcha/v1/challenge")
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
            challenge = response.json()
            self.assertEqual(challenge["algorithm"], "SHA-256")
            self.assertIn("challenge", challenge)
            self.assertIn("salt", challenge)
            self.assertIn("signature", challenge)
            self.assertIn("maxNumber", challenge)

            # Solve the v1 challenge using the altcha library
            solution = solve_challenge_v1(
                challenge=challenge["challenge"],
                salt=challenge["salt"],
                algorithm=challenge["algorithm"],
                max_number=challenge["maxNumber"],
            )
            token = base64.b64encode(
                json.dumps({**challenge, "number": solution.number}).encode()
            ).decode()

            response = test_client.get("/demo/", headers={"X-Captcha-Token": token})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), {"Hello": "World"})

    def test_valid_header_altcha_v2(self):
        with self._create_test_client() as test_client:
            response = test_client.get("/altcha/v2/challenge")
            self.assertEqual(response.status_code, status.HTTP_200_OK, response.text)
            challenge = response.json()
            self.assertIn("parameters", challenge)
            self.assertEqual(challenge["parameters"]["algorithm"], "PBKDF2/SHA-256")
            self.assertIn("cost", challenge["parameters"])
            self.assertIn("keyPrefix", challenge["parameters"])
            self.assertIn("salt", challenge["parameters"])
            self.assertIn("nonce", challenge["parameters"])
            self.assertIn("expiresAt", challenge["parameters"])
            self.assertIn("signature", challenge)

            # Solve the v2 challenge using the altcha library
            challenge = Challenge.from_dict(challenge)
            solution = solve_challenge(challenge)
            token = Payload(challenge, solution).to_base64()

            response = test_client.get("/demo/", headers={"X-Captcha-Token": token})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response.json(), {"Hello": "World"})

    def test_invalid_header_altcha_v1(self):
        with self._create_test_client() as test_client:
            with self.assertRaisesRegex(
                AccessError,
                "Altcha payload expired",
            ):
                test_client.get(
                    "/demo/",
                    headers={
                        "X-Captcha-Token": (
                            "eyJhbGdvcml0aG0iOiAiU0hBLTI1NiIsICJjaGFsbGVuZ2UiOi"
                            "AiYjI5OTQ3MjJkYTBlNGViM2VjZWI3ZGNjNGNjNjVlODcyYWI0"
                            "YTMzYzU4MjFhZjE1NGQ1NGNmMmY5Njg4MWViNiIsICJtYXhOdW"
                            "1iZXIiOiA1MDAwMCwgInNhbHQiOiAiZjZjOGQzNjZkYWIzOTVj"
                            "ZjE0ZDVjOTdhP2V4cGlyZXM9MTc3NjE4MTE1NiYiLCAic2lnbm"
                            "F0dXJlIjogImQ0Y2Q0MzYyZTdkZGE5NmU5ZjJjM2FiNWU4MmIw"
                            "YTE5YmI1ZmY3MmI0ZWFlOGI0MzJlMmY4YTkyOWE0NzI4OGUiLC"
                            "AibnVtYmVyIjogMzEwNTF9"
                        )
                    },
                )

    def test_invalid_header_altcha_v2(self):
        with self._create_test_client() as test_client:
            with self.assertRaisesRegex(
                AccessError,
                "Altcha validation failed",
            ):
                test_client.get(
                    "/demo/",
                    headers={
                        "X-Captcha-Token": (
                            "eyJjaGFsbGVuZ2UiOiB7InBhcmFtZXRlcnMiOiB7ImFsZ29yaX"
                            "RobSI6ICJQQktERjIvU0hBLTI1NiIsICJjb3N0IjogNTAwMCwg"
                            "ImtleUxlbmd0aCI6IDMyLCAia2V5UHJlZml4IjogImVhOTdmZm"
                            "YxYTI2Mjc3MTY5ZjY0YmFiNjkwNzU3MDc2IiwgIm5vbmNlIjog"
                            "IjM2YmFmMWM1MzRmYjFhNWYyOGE5YTNiMmE0ZjVmMGU1IiwgIn"
                            "NhbHQiOiAiMGM4Mzg4MWIwNzI4NDFjN2FiMDgyODQwNjAwYWI5"
                            "OWEiLCAiZXhwaXJlc0F0IjogMTc3NjE4MTM5M30sICJzaWduYX"
                            "R1cmUiOiAiYjJhM2ZkOTQ2YjBlZTllYzcxODA2OGI2YTYwM2Vl"
                            "NjAxY2RiYjNiNTg3YzkxZjE2MTUxOTY2MGEwZWFlZGU1MSJ9LC"
                            "Aic29sdXRpb24iOiB7ImNvdW50ZXIiOiA3MDQxLCAiZGVyaXZl"
                            "ZEtleSI6ICJlYTk3ZmZmMWEyNjI3NzE2OWY2NGJhYjY5MDc1Nz"
                            "A3NjMwMGY0NTJiMzgxOTgyOTljOTU1M2UxZDk5NGQyNTBmIiwg"
                            "InRpbWUiOiA0NzA5LjI1ODgzNTk5OTIwOH19"
                        )
                    },
                )
