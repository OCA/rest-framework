from typing import Annotated

from odoo import api, models

from odoo.addons.base.models.res_users import Users as ResUsers
from odoo.addons.fastapi.dependencies import (
    authenticated_partner_env,
    odoo_env,
)

from fastapi import APIRouter, Depends

from ..schemas.schemas import UserSc, UserScDel, UserScUpdate

# create a router
user_router = APIRouter(tags=["user"])


@user_router.post("/user/create")
def create_user_data(
    data: list[UserSc],
    env: Annotated[api.Environment, Depends(odoo_env)],
    partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
) -> dict:
    """
    create user personal data of authenticated user
    """

    result = {}
    for d in data:
        user = env["res.users"].search(
            ["|", ("login", "=", d.login), ("login", "=", d.email)]
        )
        if user:
            result[f"{user.name}"] = "No_modif"
        else:
            user = env["api.user.router"].create_user(d)
            result[f"{user.name}"] = "New ok"

    return result


@user_router.post("/user/update")
def update_user_data(
    data: UserScUpdate,
    env: Annotated[api.Environment, Depends(odoo_env)],
    partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
):
    """
    update user personal data of authenticated user
    """
    # UserScUpdate.to_user_vals(data)
    # helper = env["api.user.router"].new({"user": user})
    updated_user = env["api.user.router"]._update_user(data)
    if updated_user:
        return "Update OK"
    else:
        return "No update, no user found"
    #


@user_router.post("/user/archive")
def archive_user_data(
    data: UserScDel,
    env: Annotated[api.Environment, Depends(odoo_env)],
    partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
):
    """ """
    user_to_del = env["res.users"].search(
        [
            ("login", "=", data.login),
        ]
    )
    if user_to_del:
        user_to_del.active = False
        return "Archived user ok"
    else:
        return "Error"


class ApiUserRouter(models.AbstractModel):
    _name = "api.user.router"
    _description = "API User Router Helper"

    # user = fields.Many2one(comodel_name="res.users")

    def _update_user(self, data: UserScUpdate) -> ResUsers:
        user = self.env["res.users"].search([("login", "=", data.login)])
        values = self._get_user_values(data)
        user.write(values)
        # self._handle_shopinvader_customer_opt_in(data)
        return user

    def create_user(self, data: UserSc):
        vals = {
            "name": data.name,
            "login": data.email,
            "phone": data.phone,
            "mobile": data.mobile,
        }
        user = self.env["res.users"].create(vals)
        user = self._post_process_user_creation(user, data.misc)
        return user

    def _post_process_user_creation(self, user, misc):
        """inherit it to adapt to your needs"""
        user = user.write(misc)
        return user

    def _get_user_values(self, data: UserScUpdate):
        """inherit it to adapt to your needs"""
        values = data.misc
        return values
