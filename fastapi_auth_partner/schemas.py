#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from extendable_pydantic import StrictExtendableBaseModel

from pydantic import ConfigDict


class AuthLoginInput(StrictExtendableBaseModel):
    login: str
    password: str


class AuthRegisterInput(StrictExtendableBaseModel):
    name: str
    login: str
    password: str


class AuthForgetPasswordInput(StrictExtendableBaseModel):
    login: str


class AuthSetPasswordInput(StrictExtendableBaseModel):
    token: str
    password: str


class AuthPartnerResponse(StrictExtendableBaseModel):
    login: str
    model_config = ConfigDict(from_attributes=True)