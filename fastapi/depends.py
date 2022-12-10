# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from typing import TYPE_CHECKING

from odoo.api import Environment
from odoo.exceptions import AccessDenied

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .context import odoo_env_ctx

if TYPE_CHECKING:
    from .models.fastapi_endpoint import FastapiEndpoint


def odoo_env() -> Environment:
    yield odoo_env_ctx.get()


def authenticated_partner_impl() -> Partner:
    """This method has to be overriden when you create your fastapi app
    to declare the way your partner will be provided. In some case, this
    partner will come from the authentication mechanism (ex jwt token) in other cases
    it could comme from a lookup on an email received into an HTTP header ...
    See the fastapi_endpoint_demo for an exemple"""


def authenticated_partner(
    partner: Partner = Depends(authenticated_partner_impl),  # noqa: B008
) -> Partner:
    """If you need to get access to the authenticated partner into your
    enpoint, you can add a dependency into the endpoint definition on this
    method.
    This method is a safe way to declare a dependency without requiring a
    specific implementation. It depends on `authenticated_partner_impl`. The
    concrete implementation of authenticated_partner_impl has to be provided
    when the FastAPI app is created.
    This method is also responsible to put the authenticated partner id
    into the context of the current environment.
    """
    return partner.with_context(authenticated_partner_id=partner.id)


def authenticated_partner_env(
    partner: Partner = Depends(authenticated_partner),  # noqa: B008
) -> Environment:
    """Return an environment the authenticated partner id into the context"""
    return partner.env




def basic_auth_user(
    credential: HTTPBasicCredentials = Depends(HTTPBasic()),  # noqa: B008
    env: Environment = Depends(odoo_env),  # noqa: B008
) -> Users:
    username = credential.username
    password = credential.password
    try:
        uid = env["res.users"].authenticate(
            db=env.cr.dbname, login=username, password=password, user_agent_env=None
        )
        return env["res.users"].sudo().browse(uid)
    except AccessDenied as ad:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        ) from ad


def authenticated_partner_from_basic_auth_user(
    user: Users = Depends(basic_auth_user),  # noqa: B008
) -> Partner:
    return user.partner_id


def fastapi_endpoint_id() -> int:
    """This method is overriden by default to make the fastapi.endpoint record
    available for your endpoint method. To get the fastapi.enpoint record
    in your method, you just need to add a dependecy on the fastapi_endpoint method
    defined below
    """


def fastapi_endpoint(
    _id: int = Depends(fastapi_endpoint_id),  # noqa: B008
    env: Environment = Depends(odoo_env),  # noqa: B008
) -> "FastapiEndpoint":
    """Return the fastapi.endpoint record

    Be carefull, the information are returned as sudo
    """
    # TODO we should declare a technical user with read access only on the
    # fastapi.endpoint model
    return env["fastapi.endpoint"].sudo().browse(_id)
