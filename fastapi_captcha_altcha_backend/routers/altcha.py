# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import datetime
from typing import Annotated

from odoo import _
from odoo.exceptions import AccessDenied, ValidationError

from odoo.addons.fastapi.dependencies import fastapi_endpoint
from odoo.addons.fastapi.models import FastapiEndpoint

from fastapi import APIRouter, Depends

try:
    import altcha
    from altcha import ChallengeOptions, create_challenge
except ImportError:
    altcha = None

from ..schemas import AltchaChallenge

altcha_router = APIRouter(tags=["altcha"])


@altcha_router.get("/altcha/challenge")
def altcha_challenge(
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> AltchaChallenge:
    if not altcha:
        raise ValidationError(_("Altcha library is not installed."))
    secret_key = endpoint.sudo().captcha_secret_key
    if not secret_key:
        raise ValidationError(_("Captcha secret key is not set for this endpoint."))

    try:
        challenge = create_challenge(
            ChallengeOptions(
                expires=datetime.datetime.now() + datetime.timedelta(minutes=5),
                hmac_key=secret_key,
                max_number=50000,
            )
        )
        return AltchaChallenge.from_challenge(challenge)
    except Exception as e:
        raise AccessDenied(_("Failed to create Altcha challenge.")) from e
