# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Annotated

from odoo.api import Environment

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader


def apikey_authenticated_partner_impl(
    api_key: Annotated[
        str,
        Depends(
            APIKeyHeader(
                name="api-key",
                description="Odoo default apikey",
            )
        ),
    ],
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> Partner:
    uid = env["res.users.apikeys"]._check_credentials(
        scope=endpoint.apikey_auth_scope, key=api_key
    )
    partner = env["res.users"].sudo().browse(uid).exists().partner_id
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    if endpoint.user_id.id and endpoint.user_id.id != uid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect User"
        )
    return partner


def apikey_optionally_authenticated_partner_impl(
    api_key: Annotated[
        str,
        Depends(
            APIKeyHeader(
                name="api-key",
                description="Odoo default apikey",
            )
        ),
    ],
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> Partner | None:
    uid = env["res.users.apikeys"]._check_credentials(scope="fastapi", key=api_key)
    partner = env["res.users"].sudo().browse(uid).exists().partner_id
    if endpoint.user_id.id and endpoint.user_id.id != uid:
        partner = env["res.partner"]
    return partner


def apikey_authenticated_partner_env(
    partner: Annotated[Partner, Depends(apikey_authenticated_partner_impl)]
) -> Environment:
    return partner.with_context(authenticated_partner_id=partner.id).env


def apikey_authenticated_partner(
    partner: Annotated[Partner, Depends(apikey_authenticated_partner_impl)],
    partner_env: Annotated[Environment, Depends(apikey_authenticated_partner_env)],
) -> Partner:
    return partner_env["res.partner"].browse(partner.id)


def apikey_optionally_authenticated_partner_env(
    partner: Annotated[
        Partner | None, Depends(apikey_optionally_authenticated_partner_impl)
    ],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Environment:
    if partner:
        return partner.with_context(authenticated_partner_id=partner.id).env
    return env


def optionally_authenticated_partner(
    partner: Annotated[
        Partner | None, Depends(apikey_optionally_authenticated_partner_impl)
    ],
    partner_env: Annotated[
        Environment, Depends(apikey_optionally_authenticated_partner_env)
    ],
) -> Partner | None:
    if partner:
        return partner_env["res.partner"].browse(partner.id)
    return None
