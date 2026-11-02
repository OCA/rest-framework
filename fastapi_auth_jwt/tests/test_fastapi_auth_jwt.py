# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import time
from typing import Annotated, Any

import jwt

from odoo.api import Environment
from odoo.tests import tagged

from odoo.addons.base.models.res_partner import ResPartner
from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from fastapi import APIRouter, Depends

from ..dependencies import (
    AuthJwtOdooEnv,
    AuthJwtPartner,
    AuthJwtPayload,
    auth_jwt_authenticated_payload,
    auth_jwt_default_validator_name,
)

VALIDATOR = "fastapi_auth_jwt_test"
SECRET = "fastapi-auth-jwt-test-secret-with-enough-entropy"

router = APIRouter()


@router.get("/payload")
def get_payload(
    payload: Annotated[
        dict[str, Any], Depends(AuthJwtPayload(validator_name=VALIDATOR))
    ],
):
    return payload


@router.get("/default_validator")
def get_default_validator_payload(
    payload: Annotated[dict[str, Any], Depends(auth_jwt_authenticated_payload)],
):
    return payload


@router.get("/optional_payload")
def get_optional_payload(
    payload: Annotated[
        dict[str, Any] | None,
        Depends(AuthJwtPayload(validator_name=VALIDATOR, allow_unauthenticated=True)),
    ],
):
    return {"payload": payload}


@router.get("/partner")
def get_partner(
    partner: Annotated[ResPartner, Depends(AuthJwtPartner(validator_name=VALIDATOR))],
):
    return {"id": partner.id, "uid": partner.env.uid}


@router.get("/optional_partner")
def get_optional_partner(
    partner: Annotated[
        ResPartner,
        Depends(AuthJwtPartner(validator_name=VALIDATOR, allow_unauthenticated=True)),
    ],
):
    return {"id": partner.id or None}


@router.get("/env")
def get_env(
    env: Annotated[Environment, Depends(AuthJwtOdooEnv(validator_name=VALIDATOR))],
):
    return {"uid": env.uid}


@tagged("post_install", "-at_install")
class TestFastapiAuthJwt(FastAPITransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env["res.users"].create(
            {"name": "JWT user", "login": "fastapi_auth_jwt_user"}
        )
        cls.partner = cls.env["res.partner"].create(
            {"name": "JWT partner", "email": "jwt.partner@example.com"}
        )
        cls.validator = cls.env["auth.jwt.validator"].create(
            {
                "name": VALIDATOR,
                "signature_type": "secret",
                "secret_algorithm": "HS256",
                "secret_key": SECRET,
                "audience": "fastapi-test",
                "issuer": "fastapi-test-issuer",
                "user_id_strategy": "static",
                "static_user_id": cls.user.id,
                "partner_id_strategy": "email",
                "partner_id_required": False,
            }
        )
        cls.default_fastapi_router = router
        cls.default_fastapi_running_user = cls.env.ref("base.user_admin")

    def _token(self, key=SECRET, **claims):
        payload = {
            "aud": "fastapi-test",
            "iss": "fastapi-test-issuer",
            "exp": int(time.time()) + 300,
        }
        payload.update(claims)
        return jwt.encode(payload, key, algorithm="HS256")

    def _get(self, path, token=None, **kw):
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        with self._create_test_client(**kw) as client:
            return client.get(path, headers=headers)

    # --- AuthJwtPayload -----------------------------------------------------

    def test_payload_ok(self):
        response = self._get("/payload", self._token(sub="abc"))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["sub"], "abc")

    def test_payload_missing_token(self):
        self.assertEqual(self._get("/payload").status_code, 401)

    def test_payload_bad_signature(self):
        token = self._token(key="another-secret-another-secret-another-secret")
        self.assertEqual(self._get("/payload", token).status_code, 401)

    def test_payload_expired(self):
        token = self._token(exp=int(time.time()) - 60)
        self.assertEqual(self._get("/payload", token).status_code, 401)

    def test_payload_wrong_audience(self):
        token = self._token(aud="someone-else")
        self.assertEqual(self._get("/payload", token).status_code, 401)

    def test_payload_wrong_issuer(self):
        token = self._token(iss="someone-else")
        self.assertEqual(self._get("/payload", token).status_code, 401)

    def test_payload_malformed_header(self):
        with self._create_test_client() as client:
            response = client.get("/payload", headers={"Authorization": "Basic xyz"})
        self.assertEqual(response.status_code, 401)

    def test_default_validator_override(self):
        response = self._get(
            "/default_validator",
            self._token(sub="via-default"),
            dependency_overrides={auth_jwt_default_validator_name: lambda: VALIDATOR},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["sub"], "via-default")

    def test_optional_payload_without_token(self):
        response = self._get("/optional_payload")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["payload"])

    def test_optional_payload_with_invalid_token(self):
        token = self._token(exp=int(time.time()) - 60)
        self.assertEqual(self._get("/optional_payload", token).status_code, 401)

    # --- AuthJwtPartner -----------------------------------------------------

    def test_partner_ok(self):
        response = self._get("/partner", self._token(email=self.partner.email))
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["id"], self.partner.id)
        self.assertEqual(response.json()["uid"], self.user.id)

    def test_partner_not_found(self):
        token = self._token(email="nobody@example.com")
        self.assertEqual(self._get("/partner", token).status_code, 401)

    def test_partner_without_email_claim(self):
        self.assertEqual(self._get("/partner", self._token()).status_code, 401)

    def test_optional_partner_without_token(self):
        response = self._get("/optional_partner")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["id"])

    def test_optional_partner_unknown_email(self):
        token = self._token(email="nobody@example.com")
        response = self._get("/optional_partner", token)
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["id"])

    def test_optional_partner_required_by_validator(self):
        self.validator.partner_id_required = True
        token = self._token(email="nobody@example.com")
        self.assertEqual(self._get("/optional_partner", token).status_code, 401)

    # --- AuthJwtOdooEnv -----------------------------------------------------

    def test_env_runs_as_validator_user(self):
        response = self._get("/env", self._token())
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["uid"], self.user.id)

    def test_env_missing_token(self):
        self.assertEqual(self._get("/env").status_code, 401)
