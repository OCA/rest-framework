#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableSigninInput(Datamodel):
    _name = "authenticable.signin.input"

    login = fields.Str(required=True)
    password = fields.Str(required=True)


class AuthenticableSigninOutput(Datamodel):
    _name = "authenticable.signin.output"
