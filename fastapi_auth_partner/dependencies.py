# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import sys
from typing import Any, Dict, Union

from itsdangerous import URLSafeTimedSerializer
from starlette.status import HTTP_401_UNAUTHORIZED

from odoo.api import Environment

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import fastapi_endpoint, odoo_env
from odoo.addons.fastapi.models import FastapiEndpoint

from fastapi import Cookie, Depends, HTTPException, Request, Response

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

_logger = logging.getLogger(__name__)


Payload = Dict[str, Any]


class AuthPartner:
    def __init__(self, allow_unauthenticated: bool = False):
        self.allow_unauthenticated = allow_unauthenticated

    def __call__(
        self,
        request: Request,
        response: Response,
        env: Annotated[
            Environment,
            Depends(odoo_env),
        ],
        endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
        fastapi_auth_partner: Annotated[Union[str, None], Cookie()] = None,
    ) -> Partner:
        if not fastapi_auth_partner and self.allow_unauthenticated:
            return env["res.partner"].with_user(env.ref("base.public_user")).browse()

        elif fastapi_auth_partner:
            directory = endpoint.directory_id
            vals = URLSafeTimedSerializer(directory.cookie_secret_key).loads(
                fastapi_auth_partner, max_age=directory.cookie_duration * 60
            )
            if vals["did"] == directory.id and vals["pid"]:
                partner = env["res.partner"].browse(vals["pid"]).exists()
                if partner:
                    auth = partner.partner_auth_ids.filtered(
                        lambda s: s.directory_id == directory
                    )
                    if auth:
                        return partner
        _logger.info("Could not determine partner from 'fastapi_auth_partner' cookie.")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)


auth_partner_authenticated_partner = AuthPartner()

auth_partner_optionally_authenticated_partner = AuthPartner(allow_unauthenticated=True)
