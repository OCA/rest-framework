# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # guest logic should be move in an dependency module
    guest = fields.Boolean()
    partner_auth_ids = fields.One2many(
        "fastapi.auth.partner", "partner_id", "Partner Auth"
    )
