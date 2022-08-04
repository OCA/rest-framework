#  Copyright 2022 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.fields import NestedModel


class SessionLogin (Datamodel):
    _name = "session.login"

    session = NestedModel(
        'session',
        required=True,
    )
    uid = fields.Integer(
        required=True,
    )
    db = fields.String(
        required=True,
    )
