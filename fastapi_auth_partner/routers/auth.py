# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys

from odoo.exceptions import AccessError

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from odoo import SUPERUSER_ID, _, fields, models
from odoo.api import Environment

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models import FastapiEndpoint

from fastapi import APIRouter, Depends, Response
from fastapi.responses import RedirectResponse

from ..dependencies import auth_partner_authenticated_partner
from ..models.fastapi_auth_partner import COOKIE_AUTH_NAME
from ..schemas import (
    AuthForgetPasswordInput,
    AuthLoginInput,
    AuthPartnerResponse,
    AuthRegisterInput,
    AuthSetPasswordInput,
    AuthValidateEmailInput,
)

auth_router = APIRouter(tags=["auth"])


@auth_router.post("/auth/register", status_code=201)
def register(
    data: AuthRegisterInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
) -> AuthPartnerResponse:
    partner_auth = (
        env["fastapi.auth.service"].sudo()._register_auth(endpoint.directory_id, data)
    )
    partner_auth._set_auth_cookie(response)
    return AuthPartnerResponse.from_auth_partner(partner_auth)


@auth_router.post("/auth/login")
def login(
    data: AuthLoginInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
) -> AuthPartnerResponse:
    partner_auth = (
        env["fastapi.auth.service"].sudo()._login(endpoint.directory_id, data)
    )
    partner_auth._set_auth_cookie(response)
    return AuthPartnerResponse.from_auth_partner(partner_auth)


@auth_router.post("/auth/logout", status_code=205)
def logout(
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
):
    env["fastapi.auth.service"].sudo()._logout(endpoint.directory_id, response)


@auth_router.post("/auth/validate_email")
def validate_email(
    data: AuthValidateEmailInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
):
    env["fastapi.auth.service"].sudo()._validate_email(endpoint.directory_id, data)
    return {}


@auth_router.post("/auth/request_reset_password")
def request_reset_password(
    data: AuthForgetPasswordInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
):
    env["fastapi.auth.service"].sudo()._request_reset_password(
        endpoint.directory_id.id, data
    )
    return {}


@auth_router.post("/auth/set_password")
def set_password(
    data: AuthSetPasswordInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    response: Response,
) -> AuthPartnerResponse:
    partner_auth = (
        env["fastapi.auth.service"].sudo()._set_password(endpoint.directory_id, data)
    )
    partner_auth._set_auth_cookie(response)
    return AuthPartnerResponse.from_auth_partner(partner_auth)


@auth_router.get("/auth/profile")
def profile(
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
    partner: Annotated[Partner, Depends(auth_partner_authenticated_partner)],
) -> AuthPartnerResponse:
    partner_auth = partner.auth_partner_ids.filtered(
        lambda s: s.directory_id == endpoint.sudo().directory_id
    )
    return AuthPartnerResponse.from_auth_partner(partner_auth)


@auth_router.get("/auth/impersonate/{fastapi_partner_id}/{token}")
def impersonate(
    fastapi_partner_id: int,
    token: str,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> RedirectResponse:
    partner_auth = (
        env["fastapi.auth.service"]
        .sudo()
        ._impersonate(endpoint.directory_id, fastapi_partner_id, token)
    )
    base = endpoint.public_url or (
        env["ir.config_parameter"].sudo().get_param("web.base.url") + endpoint.root_path
    )
    response = RedirectResponse(url=base)
    partner_auth._set_auth_cookie(response)
    return response


class AuthService(models.AbstractModel):
    _name = "fastapi.auth.service"
    _description = "Fastapi Auth Service"

    def _prepare_partner_register(self, directory, data):
        return {
            "name": data.name,
            "email": data.login,
            "auth_partner_ids": [
                (0, 0, self._prepare_partner_auth_register(directory, data))
            ],
        }

    def _prepare_partner_auth_register(self, directory, data):
        return {
            "login": data.login,
            "password": data.password,
            "directory_id": directory.id,
        }

    def _register_auth(self, directory, data):
        vals = self._prepare_partner_register(directory, data)
        partner = self.env["res.partner"].create([vals])
        auth_partner = partner.auth_partner_ids
        auth_partner.send_registration_invite()
        return auth_partner

    def _login(self, directory, data):
        partner_auth = (
            self.env["fastapi.auth.partner"]
            .sudo()
            .log_in(directory, data.login, data.password)
        )
        if partner_auth:
            return partner_auth
        else:
            raise AccessError(_("Invalid Login or Password"))

    def _impersonate(self, directory, fastapi_partner_id, token):
        return (
            self.env["fastapi.auth.partner"]
            .sudo()
            .impersonating(directory, fastapi_partner_id, token)
        )

    def _logout(self, directory, response):
        response.set_cookie(COOKIE_AUTH_NAME, max_age=0)

    def _set_password(self, directory, data):
        partner_auth = (
            self.env["fastapi.auth.partner"]
            .sudo()
            .set_password(directory, data.token, data.password)
        )
        if partner_auth:
            partner_auth.date_last_sucessfull_reset_pwd = fields.Datetime.now()
            partner_auth.nbr_pending_reset_sent = 0
        return partner_auth

    def _request_reset_password(self, directory, data):
        self.env["fastapi.auth.partner"].with_user(
            SUPERUSER_ID
        ).with_delay().request_reset_password(directory, data.login)

    def _validate_email(self, directory, data):
        partner_auth = (
            self.env["fastapi.auth.partner"]
            .sudo()
            .validate_email(directory, data.token)
        )
        return partner_auth
