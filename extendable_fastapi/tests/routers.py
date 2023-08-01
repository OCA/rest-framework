# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from typing import Annotated

from odoo import api

from odoo.addons.fastapi.dependencies import odoo_env

from fastapi import APIRouter, Depends

from .schemas import Customer, PrivateCustomer, PrivateUser, User, UserSearchResponse

demo_pydantic_router = APIRouter(tags=["demo_pydantic"])


@demo_pydantic_router.get("/{user_id}")
def get(env: Annotated[api.Environment, Depends(odoo_env)], user_id: int) -> User:
    """
    Get a specific user using its Odoo id.
    """
    user = env["res.users"].sudo().search([("id", "=", user_id)])
    if not user:
        raise ValueError("No user found")
    return User.from_user(user)


@demo_pydantic_router.get("/private/{user_id}")
def get_private(
    env: Annotated[api.Environment, Depends(odoo_env)], user_id: int
) -> User:
    """
    Get a specific user using its Odoo id.
    """
    user = env["res.users"].sudo().search([("id", "=", user_id)])
    if not user:
        raise ValueError("No user found")
    return PrivateUser.from_user(user)


@demo_pydantic_router.post("/post_user")
def post_user(user: User) -> UserSearchResponse:
    """A demo endpoint to test the extendable pydantic model integration
    with fastapi and odoo.

    Type of the request body is User. This model is the base model
    of ExtendedUser. At runtime, the documentation and the processing
    of the request body should be done as if the type of the request body
    was ExtendedUser.
    """
    return UserSearchResponse(total=1, items=[user])


@demo_pydantic_router.post("/post_private_user")
def post_private_user(user: PrivateUser) -> User:
    """A demo endpoint to test the extendable pydantic model integration
    with fastapi and odoo.

    Type of the request body is PrivateUser. This model inherits base model
    User but does not extend it.

    This method will return attributes from the declared response type.
    It will never return attribute of a derived type from the declared response
    type, even if in the route implementation we return an instance of the
    derived type.
    """
    return user


@demo_pydantic_router.post("/post_private_user_generic")
def post_private_user_generic(user: PrivateUser) -> UserSearchResponse:
    """A demo endpoint to test the extendable pydantic model integration
    with fastapi and odoo.

    Type of the request body is PrivateUser. This model inherits base model
    User but does not extend it.

    This method will return attributes from the declared response type.
    It will never return attribute of a derived type from the declared response
    type, even if in the route implementation we return an instance of the
    derived type. This assertion is also true with generics.
    """
    return UserSearchResponse(total=1, items=[user])


@demo_pydantic_router.post("/post_private_customer")
def post_private_customer(customer: PrivateCustomer) -> Customer:
    """A demo endpoint to test the extendable pydantic model integration
    with fastapi and odoo, and more particularly the extra="forbid" config parameter.

    Type of the request body is PrivateCustomer. This model inherits base model
    Customer but does not extend it.

    This method will return attributes from the declared response type.
    It will never return attribute of a derived type from the declared response
    type, even if in the route implementation we return an instance of the
    derived type.

    Since Customer has extra fields forbidden, this route is not supposed to work.
    """
    return customer
