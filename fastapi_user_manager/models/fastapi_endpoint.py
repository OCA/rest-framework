# licenec

from typing import Annotated

from odoo import _, api, fields, models
from odoo.api import Environment
from odoo.exceptions import ValidationError

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
    odoo_env,
)

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyHeader

from ..routers.user import user_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("user_manager", "User manager")],
        ondelete={"user_manager": "cascade"},
    )

    auth_method = fields.Selection(
        selection=[("api_key", "Api key"), ("http_basic", "HTTP Basic")],
        string="Authenciation method for user manager",
    )

    def _get_fastapi_routers(self):
        if self.app == "user_manager":
            return [user_router]
        return super()._get_fastapi_routers()

    @api.constrains("app", "auth_method")
    def _valdiate_demo_auth_method(self):
        for rec in self:
            if rec.app == "user_manager" and not rec.auth_method:
                raise ValidationError(
                    _(
                        "The authentication method is required for app %(app)s",
                        app=rec.app,
                    )
                )

    @api.model
    def _fastapi_app_fields(self) -> list[str]:
        fields = super()._fastapi_app_fields()
        fields.append("auth_method")
        return fields

    def _get_app(self):
        app = super()._get_app()
        if self.app == "user_manager":
            # Here we add the overrides to the authenticated_partner_impl method
            # according to the authentication method configured on the demo app
            if self.auth_method == "http_basic":
                authenticated_partner_impl_override = (
                    authenticated_partner_from_basic_auth_user
                )
            else:
                authenticated_partner_impl_override = (
                    api_key_based_authenticated_partner_impl
                )
            app.dependency_overrides[authenticated_partner_impl] = (
                authenticated_partner_impl_override
            )
        return app


def api_key_based_authenticated_partner_impl(
    api_key: Annotated[
        str,
        Depends(
            APIKeyHeader(name="api-key", description="Api key to be log to the partner")
        ),
    ],
    env: Annotated[Environment, Depends(odoo_env)],
) -> Partner:
    partner = (
        env["res.users"]
        .sudo()
        .search([("api_key_user", "=", api_key)], limit=1)
        .partner_id
    )
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return partner
