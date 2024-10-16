# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from datetime import datetime, timedelta, timezone

from itsdangerous import URLSafeTimedSerializer

from odoo import _, fields, models, tools
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models import FastapiEndpoint

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse

from ..dependencies import auth_partner_authenticated_partner
from ..schemas import (
    AuthForgetPasswordInput,
    AuthLoginInput,
    AuthPartnerResponse,
    AuthRegisterInput,
    AuthSetPasswordInput,
    AuthValidateEmailInput,
)

COOKIE_AUTH_NAME = "fastapi_auth_partner"

auth_router = APIRouter(tags=["auth"])


@auth_router.post("/auth/register", status_code=201)
def register(
    data: AuthRegisterInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
) -> AuthPartnerResponse:
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    auth_partner = helper._signup(data)
    helper._set_auth_cookie(auth_partner, response)
    return AuthPartnerResponse.from_auth_partner(auth_partner)


@auth_router.post("/auth/login")
def login(
    data: AuthLoginInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
) -> AuthPartnerResponse:
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    auth_partner = helper._login(data)
    helper._set_auth_cookie(auth_partner, response)
    return AuthPartnerResponse.from_auth_partner(auth_partner)


@auth_router.post("/auth/logout", status_code=205)
def logout(
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
):
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    helper._logout()
    helper._clear_auth_cookie(response)
    return {}


@auth_router.post("/auth/validate_email")
def validate_email(
    data: AuthValidateEmailInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
):
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    helper._validate_email(data)
    return {}


@auth_router.post("/auth/request_reset_password")
def request_reset_password(
    data: AuthForgetPasswordInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
):
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    helper._request_reset_password(data)
    return {}


@auth_router.post("/auth/set_password")
def set_password(
    data: AuthSetPasswordInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
) -> AuthPartnerResponse:
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    auth_partner = helper._set_password(data)
    helper._set_auth_cookie(auth_partner, response)
    return AuthPartnerResponse.from_auth_partner(auth_partner)


@auth_router.get("/auth/profile")
def profile(
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    partner: Annotated[Partner, Depends(auth_partner_authenticated_partner)],
) -> AuthPartnerResponse:
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    auth_partner = helper._get_auth_from_partner(partner)
    return AuthPartnerResponse.from_auth_partner(auth_partner)


@auth_router.get("/auth/impersonate/{token}")
def impersonate(
    token: str,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> RedirectResponse:
    helper = env["fastapi.auth.service"].new({"endpoint_id": endpoint})
    auth_partner = helper._impersonate(token)
    base = (
        endpoint.public_url
        or endpoint.public_api_url
        or (
            env["ir.config_parameter"].sudo().get_param("web.base.url")
            + endpoint.root_path
        )
    )
    response = RedirectResponse(url=base)
    helper._set_auth_cookie(auth_partner, response)
    return response


class AuthService(models.AbstractModel):
    _name = "fastapi.auth.service"
    _description = "Fastapi Auth Service"

    endpoint_id = fields.Many2one("fastapi.endpoint", required=True)
    directory_id = fields.Many2one("auth.directory")

    def new(self, vals, **kwargs):
        rec = super().new(vals, **kwargs)
        # Can't have computed / related field in AbstractModel
        rec.directory_id = rec.endpoint_id.directory_id
        # Auto add endpoint context for mail context
        return rec.with_context(_fastapi_endpoint_id=vals["endpoint_id"].id)

    def _get_auth_from_partner(self, partner):
        return partner._get_auth_partner_for_directory(self.directory_id)

    def _signup(self, data):
        auth_partner = (
            self.env["auth.partner"].sudo()._signup(self.directory_id, **data.dict())
        )
        return auth_partner

    def _login(self, data):
        return self.env["auth.partner"].sudo()._login(self.directory_id, **data.dict())

    def _impersonate(self, token):
        return self.env["auth.partner"].sudo()._impersonating(self.directory_id, token)

    def _logout(self):
        pass

    def _set_password(self, data):
        return (
            self.env["auth.partner"]
            .sudo()
            ._set_password(self.directory_id, data.token, data.password)
        )

    def _request_reset_password(self, data):
        # There can be only one auth_partner per login per directory
        auth_partner = (
            self.env["auth.partner"]
            .sudo()
            .search(
                [
                    ("directory_id", "=", self.directory_id.id),
                    ("login", "=", data.login.lower()),
                ]
            )
        )

        if not auth_partner:
            # do not leak information, no partner no mail sent
            return

        return auth_partner.sudo()._request_reset_password()

    def _validate_email(self, data):
        return (
            self.env["auth.partner"]
            .sudo()
            ._validate_email(self.directory_id, data.token)
        )

    def _prepare_cookie_payload(self, partner):
        # use short key to reduce cookie size
        return {
            "did": self.directory_id.id,
            "pid": partner.id,
        }

    def _prepare_cookie(self, partner):
        secret = self.directory_id.cookie_secret_key or self.directory_id.secret_key
        if not secret:
            raise ValidationError(_("No cookie secret key defined"))
        payload = self._prepare_cookie_payload(partner)
        value = URLSafeTimedSerializer(secret).dumps(payload)
        exp = (
            datetime.now(timezone.utc)
            + timedelta(minutes=self.directory_id.cookie_duration)
        ).timestamp()
        vals = {
            "value": value,
            "expires": exp,
            "httponly": True,
            "secure": True,
            "samesite": "strict",
        }
        if tools.config.get("test_enable"):
            # do not force https for test
            vals["secure"] = False
        return vals

    def _set_auth_cookie(self, auth_partner, response):
        response.set_cookie(
            COOKIE_AUTH_NAME, **self.sudo()._prepare_cookie(auth_partner.partner_id)
        )

    def _clear_auth_cookie(self, response):
        response.set_cookie(COOKIE_AUTH_NAME, max_age=0)
