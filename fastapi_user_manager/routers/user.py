from typing import Annotated

from odoo import api, models
from odoo.fields import Command

from odoo.addons.fastapi.dependencies import (
    authenticated_partner_env,
    odoo_env,
)

from fastapi import APIRouter, Depends

from ..schemas.schemas import UserSc

# create a router
user_router = APIRouter(tags=["user"])


@user_router.post("/user")
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
        user, error = env["api.user.router"]._write_user(d)
        if user:
            result[f"{user.login}"] = "Write ok"
            if error:
                for e in error:
                    result[f"{user.login}/{e}"] = error[e]
        else:
            result[f"{d.login}"] = "Error login"

    return result


# @user_router.post("/user/update")
# def update_user_data(
#     data: list[UserScUpdate],
#     env: Annotated[api.Environment, Depends(odoo_env)],
#     partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
# ):
#     """
#     update user personal data of authenticated user
#     """
#     # UserScUpdate.to_user_vals(data)
#     # helper = env["api.user.router"].new({"user": user})
#     result = {}
#     for d in data:
#         updated_user = env["api.user.router"]._update_user(d)
#         if updated_user:
#             result[f"{updated_user.login}"] = "Update ok"
#         else:
#             result[f"{d.login}"] = "No_modif"
#     return result
#
#
# @user_router.post("/user/archive")
# def archive_user_data(
#     data: list[UserScDel],
#     env: Annotated[api.Environment, Depends(odoo_env)],
#     partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
# ):
#     """ """
#     result = {}
#     for d in data:
#         user_to_del = env["res.users"].search(
#             [
#                 ("login", "=", data.login),
#             ]
#         )
#         if user_to_del:
#             user_to_del.active = False
#             result[f"{user_to_del.login}"] = "Archived user ok"
#         else:
#             result[f"{d.login}"] = "ERROR No login"
#     return result


class ApiUserRouter(models.AbstractModel):
    _name = "api.user.router"
    _description = "API User Router Helper"

    # user = fields.Many2one(comodel_name="res.users")
    def _write_user(self, data: UserSc):
        vals, error = self._get_user_values(data)
        user = self.env["res.users"].search([("login", "=", data.login)])
        if user:
            user.sudo().write(vals)
            user, error = self._post_process_user_update(user, data.misc, error)
        else:
            user = self.env["res.users"].sudo().create(vals)
            user, error = self._post_process_user_creation(user, data.misc, error)
        return user, error

    def _post_process_user_update(self, user, misc, error):
        """inherit it to adapt to your needs"""
        return user, error

    def _post_process_user_creation(self, user, misc, error):
        """inherit it to adapt to your needs"""
        return user, error

    def _get_user_values(self, data: UserSc):
        """inherit it to adapt to your needs"""
        vals = data.misc.copy()
        error = {}
        if "login" not in vals:
            vals["login"] = data.login
        if "company" in vals:
            vals_company = vals.pop("company")
            company_id = self.env["res.company"].search([("code", "in", vals_company)])
            if company_id:
                if len(vals_company) != len(company_id):
                    list_company_id = []
                    for x in company_id:
                        list_company_id.append(x.code)
                    error["company"] = f"{list_company_id} for {vals_company}"
                vals["company_ids"] = [Command.link(comp) for comp in company_id.ids]
                vals["company_id"] = company_id[0].id
            else:
                error["company"] = "no company found"
                vals["company_id"] = self.env.company.id
        if "roles" in vals:
            vals_roles = vals.pop("roles")
            if hasattr(self.env["res.users"], "role_ids"):
                roles = self.env["res.users.role"].search([("name", "in", vals_roles)])
                if roles:
                    if len(vals_roles) != len(roles):
                        error["roles"] = "not all roles have been found"
                    vals["role_line_ids"] = [
                        Command.create({"role_id": rol_id}) for rol_id in roles.ids
                    ]
                else:
                    error["roles"] = "Error no roles found"
            else:
                raise NotImplementedError
        if "group" in vals:
            vals.pop("group")
            raise NotImplementedError
        return vals, error
