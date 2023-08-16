#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from extendable_pydantic import ExtendableModelMeta
from pydantic import BaseModel

from odoo.addons.pydantic import utils


class AuthLoginInput(BaseModel, metaclass=ExtendableModelMeta):
    login: str
    password: str


class AuthRegisterInput(BaseModel, metaclass=ExtendableModelMeta):
    name: str
    login: str
    password: str


class AuthForgetPasswordInput(BaseModel, metaclass=ExtendableModelMeta):
    login: str


class AuthSetPasswordInput(BaseModel, metaclass=ExtendableModelMeta):
    token: str
    password: str


class AuthPartnerResponse(BaseModel, metaclass=ExtendableModelMeta):
    login: str

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
