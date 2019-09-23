# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class PartnerInfo(Datamodel):
    _name = "partner.info"
    _inherit = "partner.short.info"

    street = fields.String(required=True, allow_none=False)
    street2 = fields.String(required=False, allow_none=True)
    zip_code = fields.String(required=True, allow_none=False)
    city = fields.String(required=True, allow_none=False)
    phone = fields.String(required=False, allow_none=True)
    state = NestedModel("state.info")
    country = NestedModel("country.info")
    is_componay = fields.Boolean(required=False, allow_none=False)
