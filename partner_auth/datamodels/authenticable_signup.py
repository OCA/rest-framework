#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableSignupInput(Datamodel):
    _name = "authenticable.signup.input"

    login = fields.Str(required=True)
    password = fields.Str(required=True)
    backend = fields.NestedModel("authenticable.backend", required=True)


class AuthenticableSignupOutput(Datamodel):
    _name = "authenticable.signup.output"

    result = fields.Boolean(required=True)
