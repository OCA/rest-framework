from typing import Annotated

from odoo import api, models
from odoo.fields import Command

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
    data: list[UserScUpdate],
    env: Annotated[api.Environment, Depends(odoo_env)],
    partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
):
    """
    update user personal data of authenticated user
    """
    # UserScUpdate.to_user_vals(data)
    # helper = env["api.user.router"].new({"user": user})
    result = {}
    for d in data:
        updated_user = env["api.user.router"]._update_user(d)
        if updated_user:
            result[f"{updated_user.login}"] = "Update ok"
        else:
            result[f"{d.login}"] = "No_modif"
    return result


@user_router.post("/user/archive")
def archive_user_data(
    data: list[UserScDel],
    env: Annotated[api.Environment, Depends(odoo_env)],
    partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
):
    """ """
    result = {}
    for d in data:
        user_to_del = env["res.users"].search(
            [
                ("login", "=", data.login),
            ]
        )
        if user_to_del:
            user_to_del.active = False
            result[f"{user_to_del.login}"] = "Archived user ok"
        else:
            result[f"{d.login}"] = "ERROR No login"
    return result


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
            "login": data.login,
            "email": data.email,
            "phone": data.phone,
            "mobile": data.mobile,
        }
        company_id = self.env["res.company"].search([("name", "=", data.company)])
        vals["company_id"] = company_id.id if company_id else False
        if hasattr(self.env["res.users"], "role_ids"):
            roles = self.env["res.users.role"].search([("name", "in", data.role)])
            vals["role_line_ids"] = [
                Command.create({"role_id": rol_id}) for rol_id in roles.ids
            ]
        user = self.env["res.users"].create(vals)
        user = self._post_process_user_creation(user, data.misc)
        return user

    def _post_process_user_creation(self, user, misc):
        """inherit it to adapt to your needs"""
        if misc:
            user = user.write(misc)
        return user

    def _get_user_values(self, data: UserScUpdate):
        """inherit it to adapt to your needs"""
        values = data.misc
        return values
