# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # guest logic should be move in an dependency module
    guest = fields.Boolean()
    auth_partner_ids = fields.One2many(
        "fastapi.auth.partner", "partner_id", "Partner Auth"
    )
    count_partner_auth = fields.Integer(compute="_compute_count_partner_auth")

    def _compute_count_partner_auth(self):
        data = self.env["fastapi.auth.partner"].read_group(
            [
                ("partner_id", "in", self.ids),
            ],
            ["partner_id"],
            groupby=["partner_id"],
            lazy=False,
        )
        res = {item["partner_id"][0]: item["__count"] for item in data}

        for record in self:
            record.count_partner_auth = res.get(record.id, 0)
