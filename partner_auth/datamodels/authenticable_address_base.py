#  Copyright (c) Akretion 2020
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AuthenticableAddressBase(Datamodel):
    _name = "authenticable.address.base"

    name = fields.Str(required=True)
    date = fields.Date(required=True)
    street = fields.Str(required=True)
    street2 = fields.Str()
    zip = fields.Int(required=True)
    city = fields.Str(required=True)
    email = fields.Email()
