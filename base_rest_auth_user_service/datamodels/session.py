#  Copyright 2022 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from marshmallow import fields

from odoo.addons.datamodel.core import Datamodel


class Session (Datamodel):
    _name = 'session'

    sid = fields.String(
        required=True,
    )
    expires_at = fields.DateTime()
