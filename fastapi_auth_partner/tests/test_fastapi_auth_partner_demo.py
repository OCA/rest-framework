# Copyright 2023 ACSONE SA/NV
# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import sys

from odoo import tests

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi_auth_partner.dependencies import AuthPartner

from fastapi import Depends, status

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from odoo.addons.fastapi_auth_partner.routers.auth import auth_router
from odoo.addons.fastapi_auth_partner.schemas import AuthPartnerResponse


@auth_router.get("/auth/whoami-public-or-partner")
def whoami_public_or_partner(
    partner: Annotated[
        Partner,
        Depends(AuthPartner(allow_unauthenticated=True)),
    ],
) -> AuthPartnerResponse:
    if partner:
        return AuthPartnerResponse.from_auth_partner(partner.auth_partner_ids)
    return AuthPartnerResponse(login="no-one", mail_verified=False)


@tests.tagged("post_install", "-at_install")
class TestEndToEnd(tests.HttpCase):
    def setUp(self):
        super().setUp()
        endpoint = self.env.ref("fastapi_auth_partner.fastapi_endpoint_demo")
        endpoint._handle_registry_sync()

        self.fastapi_demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
        self.fastapi_demo_app._handle_registry_sync()

    def _register_partner(self):
        return self.url_open(
            "/fastapi_auth_partner_demo/auth/register",
            timeout=1000,
            data=json.dumps(
                {
                    "name": "Loriot",
                    "login": "loriot@example.org",
                    "password": "supersecret",
                }
            ),
        )

    def test_register(self):
        response = self._register_partner()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.json(), {"login": "loriot@example.org", "mail_verified": False}
        )
        self.assertIn("fastapi_auth_partner", response.cookies)

    def test_profile(self):
        self._register_partner()
        resp = self.url_open("/fastapi_auth_partner_demo/auth/profile")
        resp.raise_for_status()
        data = resp.json()
        self.assertEqual(
            data,
            {"login": "loriot@example.org", "mail_verified": False},
        )

    def test_profile_forbidden(self):
        """A end-to-end test with negative authentication."""
        resp = self.url_open("/fastapi_auth_partner_demo/auth/profile")
        self.assertEqual(resp.status_code, 401)

    def test_public(self):
        """A end-to-end test for anonymous/public access."""
        resp = self.url_open("/fastapi_auth_partner_demo/auth/whoami-public-or-partner")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"login": "no-one", "mail_verified": False})

        self._register_partner()
        resp = self.url_open("/fastapi_auth_partner_demo/auth/whoami-public-or-partner")
        self.assertEqual(
            resp.json(), {"login": "loriot@example.org", "mail_verified": False}
        )
