from typing import Annotated

from odoo import api, models

from odoo.addons.base.models.res_users import Users as ResUsers
from odoo.addons.fastapi.dependencies import (
    authenticated_partner_env,
    odoo_env,
)

from fastapi import APIRouter, Depends

from ..schemas.schemas import UserSc, UserScUpdate

# create a router
user_router = APIRouter(tags=["user"])


@user_router.post("/user")
def update_user_data(
    data: UserSc,
    env: Annotated[api.Environment, Depends(odoo_env)],
    partner: Annotated[api.Environment, Depends(authenticated_partner_env)],
    # user: Annotated[ResUsers, Depends(odoo_env)],
) -> UserSc:
    """
    update user personal data of authenticated user
    """
    user = env["res.users"].search(
        [("name", "=", data.name), ("email", "=", data.email)]
    )
    if user:
        return UserSc.from_res_user(user)
    else:
        vals = {
            "name": data.name,
            "login": data.email,
            "phone": data.phone,
            "mobile": data.mobile,
        }
        user = env["res.users"].create(vals)
        return UserSc.from_res_user(user)
    # helper = env["api.user.router"].new()
    # user = helper.create(data)
    # return UserSc.from_res_user(user)


# def update_user_data(
#     data: UserScUpdate,
#     env: Annotated[api.Environment, Depends(odoo_env)],
#     # env: Annotated[api.Environment, Depends(authenticated_partner_env)],
#     # user: Annotated[ResUsers, Depends(odoo_env)],
# ) -> ResUsers:
#     """
#     update user personal data of authenticated user
#     """
#     UserScUpdate.to_user_vals(data)
#     helper = env["api.user.router"].new({"user": user})
#     updated_user = helper._update_user(data)
#     return UserSc.from_res_user(updated_user)


class ApiUserRouter(models.AbstractModel):
    _name = "api.user.router"
    _description = "API User Router Helper"

    # user = fields.Many2one(comodel_name="res.users")

    def _update_user(self, data: UserScUpdate) -> ResUsers:
        self.ensure_one()
        values = self._get_user_values(data)
        user = self.user
        user.write(values)
        # self._handle_shopinvader_customer_opt_in(data)
        return user

    def _create_user(self, data: UserSc) -> ResUsers:
        self.ensure_one()
        user = self.env["res.users"].search(
            [("name", "=", data.name), ("email", "=", data.email)]
        )
        if user:
            return user
        else:
            vals = {
                "name": data.name,
                "email": data.email,
                "phone": data.phone,
                "mobile": data.mobile,
            }
            user = self.env["res.users"].create(vals)
            return user

    # def _get_user_values(self, data: CustomerUpdate) -> dict:
    #     values = data.to_user_vals()
    #     lang_id = data.lang_id
    #     if bool(lang_id):
    #         values["lang"] = self.env["res.lang"].browse(lang_id).code
    #     return values


# @user_router.get("/users", response_model=list[UserInfo])
# def get_users(env: Annotated[Environment, Depends(odoo_env)]) -> list[UserInfo]:
#     return [
#             UserInfo(name=user.name, email=user.email or "")
#             for user in env["res.users"].search([])
#         ]


# @customer_router.get("/customer")
# def get_customer_data(
#     partner: Annotated[ResPartner, Depends(authenticated_partner)],
# ) -> Customer:
#     """
#     Get customer personal data of authenticated user
#     """
#     return Customer.from_res_partner(partner)


# @customer_router.post(
#     "/customer",
# )
# def update_customer_data(
#     data: CustomerUpdate,
#     env: Annotated[api.Environment, Depends(authenticated_partner_env)],
#     partner: Annotated[ResPartner, Depends(authenticated_partner)],
# ) -> Customer:
#     """
#     update customer personal data of authenticated user
#     """
#     CustomerUpdate.to_res_partner_vals(data)
#     helper = env["shopinvader_api_customer.router.helper"].new({"partner": partner})
#     updated_partner = helper._update_shopinvader_customer(data)
#     return Customer.from_res_partner(updated_partner)
