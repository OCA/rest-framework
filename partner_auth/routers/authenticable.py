# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import sys
from datetime import datetime, timedelta

from odoo.exceptions import AccessError, ValidationError
from odoo.http import request

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from fastapi import APIRouter, Depends
from itsdangerous import URLSafeTimedSerializer

from odoo import _, models, tools
from odoo.api import Environment

from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models import FastapiEndpoint

from ..schemas import (
    AuthForgetPasswordInput,
    AuthLoginInput,
    AuthPartnerResponse,
    AuthRegisterInput,
    AuthSetPasswordInput,
)

auth_router = APIRouter(tags=["auth"])


COOKIE_AUTH_NAME = "partner_auth"


@auth_router.post("/auth/register", status_code=201)
def register(
    data: AuthRegisterInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> AuthPartnerResponse:
    partner_auth = env["auth.service"]._register_auth(endpoint.directory_id, data)
    return AuthPartnerResponse.from_orm(partner_auth)


@auth_router.post("/auth/login")
def login(
    data: AuthLoginInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> AuthPartnerResponse:
    partner_auth = env["auth.service"]._login(endpoint.directory_id, data)
    return AuthPartnerResponse.from_orm(partner_auth)


@auth_router.post("/auth/logout", status_code=205)
def logout(
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
):
    env["auth.service"]._logout(endpoint.directory_id)


@auth_router.post("/auth/forget_password")
def forget_password(
    data: AuthForgetPasswordInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
):
    env["auth.service"]._forget_password(endpoint.directory_id, data)


@auth_router.post("/auth/set_password")
def set_password(
    data: AuthSetPasswordInput,
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> AuthPartnerResponse:
    partner_auth = env["auth.service"]._set_password(endpoint.directory_id, data)
    return AuthPartnerResponse.from_orm(partner_auth)


class AuthService(models.AbstractModel):
    _name = "auth.service"
    _description = "Auth Service"

    def _prepare_partner_register(self, data):
        return {
            "name": data.name,
            "email": data.login,
        }

    def _prepare_partner_auth_register(self, data):
        return {
            "login": data.login,
            "password": data.password,
        }

    def _register_auth(self, directory, data):
        vals = self._prepare_partner_register(data)
        partner = self.env["res.partner"].create([vals])
        vals = self._prepare_partner_auth_register(data)
        vals.update({"partner_id": partner.id, "directory_id": directory.id})
        partner_auth = self.env["partner.auth"].create(vals)
        self._set_auth_cookie(partner_auth)
        return partner_auth

    def _prepare_cookie_payload(self, partner_auth):
        # use short key to reduce cookie size
        return {
            "did": self.partner_auth.directory_id.id,
            "pid": partner_auth.partner_id.id,
        }

    def _prepare_cookie(self, partner_auth):
        secret = partner_auth.directory_id.cookie_secret_key
        if not secret:
            raise ValidationError(_("No cookie secret key defined"))
        payload = self._prepare_cookie_payload(partner_auth)
        value = URLSafeTimedSerializer(secret).dumps(payload)
        exp = (
            datetime.utcnow()
            + timedelta(minutes=partner_auth.directory_id.cookie_duration)
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

    def _set_auth_cookie(self, partner_auth):
        if request:
            request.future_response.set_cookie(
                COOKIE_AUTH_NAME, **self._prepare_cookie(partner_auth)
            )

    def _login(self, directory, data):
        partner_auth = (
            self.env["partner.auth"].sudo().log_in(directory, data.login, data.password)
        )
        if partner_auth:
            self._set_auth_cookie(partner_auth)
            return partner_auth
        else:
            raise AccessError(_("Invalid Login or Password"))

    def _logout(self, directory):
        if request:
            request.future_response.set_cookie(COOKIE_AUTH_NAME, max_age=0)

    def _set_password(self, directory, data):
        partner_auth = (
            self.env["partner.auth"]
            .sudo()
            .set_password(directory, data.token_set_password, data.password)
        )
        self._set_auth_cookie(partner_auth)
        return partner_auth

    def _forget_password(self, directory, data):
        self.env["partner.auth"].sudo().with_delay().forget_password(
            directory, data.login
        )
