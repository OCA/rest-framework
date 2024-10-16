# Copyright 2024 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from extendable_pydantic import StrictExtendableBaseModel


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


class AuthValidateEmailInput(StrictExtendableBaseModel):
    token: str


class AuthPartnerResponse(StrictExtendableBaseModel):
    login: str
    mail_verified: bool

    @classmethod
    def from_auth_partner(cls, odoo_rec):
        return cls.model_construct(
            login=odoo_rec.login, mail_verified=odoo_rec.mail_verified
        )
