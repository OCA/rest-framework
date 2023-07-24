# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from fastapi import APIRouter

from .schemas import PrivateUser, User, UserSearchResponse

demo_pydantic_router = APIRouter(tags=["demo_pydantic"])


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
def post_private_user(user: PrivateUser) -> UserSearchResponse:
    """A demo endpoint to test the extendable pydantic model integration
    with fastapi and odoo.

    Type of the request body is PrivateUser. This model inherits base model
    User.
    """
    return UserSearchResponse(total=1, items=[user])
