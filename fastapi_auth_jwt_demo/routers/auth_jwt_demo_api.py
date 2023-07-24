# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from typing import Annotated, Union

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi_auth_jwt.dependencies import AuthJwtPartner

from fastapi import APIRouter, Depends
from pydantic import BaseModel


class TestData(BaseModel):
    name: Union[str, None] = None
    email: Union[str, None] = None
    uid: int


router = APIRouter()


@router.get("/whoami", response_model=TestData)
def whoami(
    partner: Annotated[
        Partner,
        Depends(AuthJwtPartner(validator_name="demo")),
    ],
) -> TestData:
    return TestData(
        name=partner.name,
        email=partner.email,
        uid=partner.env.uid,
    )


@router.get("/whoami-public-or-jwt", response_model=TestData)
def whoami_public_or_jwt(
    partner: Annotated[
        Partner,
        Depends(AuthJwtPartner(validator_name="demo", allow_unauthenticated=True)),
    ],
):
    if partner:
        return TestData(
            name=partner.name,
            email=partner.email,
            uid=partner.env.uid,
        )
    return TestData(uid=partner.env.uid)


@router.get("/cookie/whoami", response_model=TestData)
def whoami_cookie(
    partner: Annotated[
        Partner,
        Depends(AuthJwtPartner(validator_name="demo_cookie")),
    ],
):
    return TestData(
        name=partner.name,
        email=partner.email,
        uid=partner.env.uid,
    )


@router.get("/cookie/whoami-public-or-jwt", response_model=TestData)
def whoami_cookie_public_or_jwt(
    partner: Annotated[
        Partner,
        Depends(
            AuthJwtPartner(validator_name="demo_cookie", allow_unauthenticated=True)
        ),
    ],
):
    if partner:
        return TestData(
            name=partner.name,
            email=partner.email,
            uid=partner.env.uid,
        )
    return TestData(uid=partner.env.uid)


@router.get("/keycloak/whoami", response_model=TestData)
def whoami_keycloak(
    partner: Annotated[
        Partner, Depends(AuthJwtPartner(validator_name="demo_keycloak"))
    ],
):
    return TestData(
        name=partner.name,
        email=partner.email,
        uid=partner.env.uid,
    )


@router.get("/keycloak/whoami-public-or-jwt", response_model=TestData)
def whoami_keycloak_public_or_jwt(
    partner: Annotated[
        Partner,
        Depends(
            AuthJwtPartner(validator_name="demo_keycloak", allow_unauthenticated=True)
        ),
    ],
):
    if partner:
        return TestData(
            name=partner.name,
            email=partner.email,
            uid=partner.env.uid,
        )
    return TestData(uid=partner.env.uid)
