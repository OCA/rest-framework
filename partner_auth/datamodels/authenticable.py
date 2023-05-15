#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableLoginInput(Datamodel):
    _name = "authenticable.login.input"

    login = fields.Str(required=True)
    password = fields.Str(required=True)


class AuthenticableRegisterInput(Datamodel):
    _name = "authenticable.register.input"

    name = fields.Str(required=True)
    login = fields.Str(required=True)
    password = fields.Str(required=True)


class AuthenticableLoginOutput(Datamodel):
    _name = "authenticable.login.output"


class AuthenticableForgetPasswordInput(Datamodel):
    _name = "authenticable.forget.password.input"

    login = fields.Str(required=True)


class AuthenticableSetPasswordInput(Datamodel):
    _name = "authenticable.set.password.input"

    token_set_password = fields.Str(required=True)
    password = fields.Str(required=True)
