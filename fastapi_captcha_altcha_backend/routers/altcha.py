# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
import secrets
from typing import Annotated

from odoo import _
from odoo.exceptions import AccessDenied, ValidationError

from odoo.addons.fastapi.dependencies import fastapi_endpoint
from odoo.addons.fastapi.models import FastapiEndpoint

from fastapi import APIRouter, Depends

try:
    import altcha
    from altcha import create_challenge, create_challenge_v1
except ImportError:
    altcha = None


altcha_router = APIRouter(tags=["altcha"])


@altcha_router.get("/altcha/v2/challenge")
def altcha_challenge_v2(
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> dict:
    if not altcha:
        raise ValidationError(_("Altcha library is not installed."))
    secret_key = endpoint.sudo().captcha_secret_key
    if not secret_key:
        raise ValidationError(_("Captcha secret key is not set for this endpoint."))

    try:
        challenge = create_challenge(
            algorithm="PBKDF2/SHA-256",
            cost=5000,
            counter=secrets.randbelow(5000) + 5000,
            hmac_secret=secret_key,
            expires_at=datetime.datetime.now() + datetime.timedelta(minutes=5),
        )

        return challenge.to_dict()
    except Exception as e:
        raise AccessDenied(_("Failed to create Altcha challenge.")) from e


@altcha_router.get("/altcha/challenge", deprecated=True)
@altcha_router.get("/altcha/v1/challenge")
def altcha_challenge_v1(
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> dict:
    if not altcha:
        raise ValidationError(_("Altcha library is not installed."))
    secret_key = endpoint.sudo().captcha_secret_key
    if not secret_key:
        raise ValidationError(_("Captcha secret key is not set for this endpoint."))

    try:
        challenge = create_challenge_v1(
            expires=datetime.datetime.now() + datetime.timedelta(minutes=5),
            hmac_key=secret_key,
            max_number=50000,
        )

        return challenge.to_dict()
    except Exception as e:
        raise AccessDenied(_("Failed to create Altcha challenge.")) from e
