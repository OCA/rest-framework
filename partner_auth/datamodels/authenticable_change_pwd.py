#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableChangePwdInput(Datamodel):
    _name = "authenticable.change.pwd.input"

    authenticable_identifier = fields.Str(required=True)
    password = fields.Str(required=True)


class AuthenticableChangePwdOutput(Datamodel):
    _name = "authenticable.change.pwd.output"

    result = fields.Str(required=True)
