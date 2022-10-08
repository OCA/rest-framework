# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from odoo.api import Environment
from odoo.exceptions import AccessDenied

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .context import odoo_env_ctx


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
    specific implementation. It depends on `authenticated_partner_id`. The
    concrete implementation of authenticated_partner_id has to be provide
    when the FastAPI app is created.
    """
    return partner


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
        return env["res.users"].browse(uid)
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
