# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
from enum import Enum
from typing import List

from odoo import _, api, fields, models
from odoo.api import Environment
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError

from odoo.addons.base.models.res_partner import Partner

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

from ..depends import (
    authenticated_partner,
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
    fastapi_endpoint,
    odoo_env,
)


class FastapiEndpoint(models.Model):

    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
    )
    demo_auth_method = fields.Selection(
        selection=[("api_key", "Api Key"), ("http_basic", "HTTP Basic")],
        string="Authenciation method",
    )

    def _get_fastapi_routers(self) -> List[APIRouter]:
        if self.app == "demo":
            return [demo_api_router]
        return super()._get_fastapi_routers()

    @api.constrains("app", "demo_auth_method")
    def _valdiate_demo_auth_method(self):
        for rec in self:
            if rec.app == "demo" and not rec.demo_auth_method:
                raise ValidationError(
                    _(
                        "The authentication method is required for app %(app)s",
                        app=rec.app,
                    )
                )

    @api.model
    def _fastapi_app_fields(self) -> List[str]:
        fields = super()._fastapi_app_fields()
        fields.append("demo_auth_method")
        return fields

    def _get_app(self):
        app = super()._get_app()
        if self.app == "demo":
            # Here we add the overrides to the authenticated_partner_impl method
            # according to the authentication method configured on the demo app
            if self.demo_auth_method == "http_basic":
                authenticated_partner_impl_override = (
                    authenticated_partner_from_basic_auth_user
                )
            else:
                authenticated_partner_impl_override = (
                    api_key_based_authenticated_partner_impl
                )
            app.dependency_overrides[
                authenticated_partner_impl
            ] = authenticated_partner_impl_override
        return app


class UserInfo(BaseModel):
    name: str
    display_name: str


class EndpointAppInfo(BaseModel):
    id: str
    name: str
    app: str
    auth_method: str = Field(alias="demo_auth_method")
    root_path: str

    class Config:
        orm_mode = True


demo_api_router = APIRouter()


@demo_api_router.get("/")
async def hello_word():
    """Hello World!"""
    return {"Hello": "World"}


class ExceptionType(str, Enum):
    user_error = "UserError"
    validation_error = "ValidationError"
    access_error = "AccessError"
    missing_error = "MissingError"
    http_exception = "HTTPException"
    bare_exception = "BareException"


@demo_api_router.get("/exception")
async def exception(exception_type: ExceptionType, error_message: str):
    """Raise an exception

    This method is used in the test suite to check that any exception
    is correctly handled by the fastapi endpoint and that the transaction
    is roll backed.
    """
    exception_classes = {
        ExceptionType.user_error: UserError,
        ExceptionType.validation_error: ValidationError,
        ExceptionType.access_error: AccessError,
        ExceptionType.missing_error: MissingError,
        ExceptionType.http_exception: HTTPException,
        ExceptionType.bare_exception: NotImplementedError,  # any exception child of Exception
    }
    exception_cls = exception_classes[exception_type]
    if exception_cls is HTTPException:
        raise exception_cls(status_code=status.HTTP_409_CONFLICT, detail=error_message)
    raise exception_classes[exception_type](error_message)


@demo_api_router.get("/lang")
async def get_lang(env: Environment = Depends(odoo_env)):  # noqa: B008
    """Returns the language according to the available languages in Odoo and the
    Accept-Language header.

    This method is used in the test suite to check that the language is correctly
    set in the Odoo environment according to the Accept-Language header
    """
    return env.context.get("lang")


@demo_api_router.get("/who_ami", response_model=UserInfo)
async def who_ami(partner=Depends(authenticated_partner)) -> UserInfo:  # noqa: B008
    """Who am I?

    Returns the authenticated partner
    """
    # This method show you how you can rget the authenticated partner without
    # depending on a specific implementation.
    return UserInfo(name=partner.name, display_name=partner.display_name)


@demo_api_router.get(
    "/endpoint_app_info",
    response_model=EndpointAppInfo,
    dependencies=[Depends(authenticated_partner)],
)
async def endpoint_app_info(
    endpoint: FastapiEndpoint = Depends(fastapi_endpoint),  # noqa: B008
) -> EndpointAppInfo:
    """Returns the current endpoint configuration"""
    # This method show you how to get access to current endpoint configuration
    # It also show you how you can specify a dependency to force the security
    # even if the method doesn't require the authenticated partner as parameter
    return EndpointAppInfo.from_orm(endpoint)


def api_key_based_authenticated_partner_impl(
    api_key: str = Depends(  # noqa: B008
        APIKeyHeader(
            name="api-key",
            description="In this demo, you can use a user's login as api key.",
        )
    ),
    env: Environment = Depends(odoo_env),  # noqa: B008
) -> Partner:
    """A dummy implementation that look for a user with the same login
    as the provided api key
    """
    partner = (
        env["res.users"].sudo().search([("login", "=", api_key)], limit=1).partner_id
    )
    if not partner:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect API Key"
        )
    return partner
