#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableSignoutInput(Datamodel):
    _name = "authenticable.signout.input"

    authenticable_identifier = fields.Str(required=True)


class AuthenticableSignoutOutput(Datamodel):
    _name = "authenticable.signout.output"

    result = fields.Boolean(required=True)
