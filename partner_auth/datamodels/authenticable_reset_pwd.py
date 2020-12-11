#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableResetPwdInput(Datamodel):
    _name = "authenticable.reset.pwd.input"

    authenticable_identifier = fields.Str(required=True)
    backend = fields.NestedModel("authenticable.backend")


class AuthenticableSigninOutput(Datamodel):
    _name = "authenticable.reset.pwd.output"

    result = fields.Boolean(required=True)
