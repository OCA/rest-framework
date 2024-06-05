# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from typing import Annotated

from odoo import SUPERUSER_ID
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.auth_api_key.models.auth_api_key import AuthApiKey
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models.fastapi_endpoint import FastapiEndpoint

from fastapi import Depends, status
from fastapi.exceptions import HTTPException
from fastapi.security import APIKeyHeader


def authenticated_auth_api_key(
    key: Annotated[str, Depends(APIKeyHeader(name="HTTP-API-KEY"))],
    env: Annotated[Environment, Depends(odoo_env)],
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> AuthApiKey:
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No HTTP-API-KEY provided",
            headers={"WWW-Authenticate": "HTTP-API-KEY"},
        )
    admin_env = Environment(env.cr, SUPERUSER_ID, {})
    try:
        auth_api_key = admin_env["auth.api.key"]._retrieve_api_key(key)
    except ValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error.args,
            headers={"WWW-Authenticate": "HTTP-API-KEY"},
        ) from error
    # Ensure the api key is authorized for the current endpoint.
    if auth_api_key not in endpoint.sudo().auth_api_key_group_id.auth_api_key_ids:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "HTTP-API-KEY"},
        )
    return auth_api_key


def authenticated_partner_by_api_key(
    auth_api_key: Annotated[AuthApiKey, Depends(authenticated_auth_api_key)]
) -> Partner:
    return auth_api_key.user_id.partner_id


def authenticated_env_by_auth_api_key(
    auth_api_key: Annotated[AuthApiKey, Depends(authenticated_auth_api_key)]
) -> Environment:
    # set api key id in context
    return auth_api_key.with_user(auth_api_key.user_id).env
