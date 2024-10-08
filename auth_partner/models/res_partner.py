# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    # guest logic should be moved in an dependency module
    guest = fields.Boolean()
    auth_partner_ids = fields.One2many("auth.partner", "partner_id", "Partner Auth")
    auth_partner_count = fields.Integer(
        compute="_compute_auth_partner_count", compute_sudo=True
    )

    def _compute_auth_partner_count(self):
        data = self.env["auth.partner"].read_group(
            [
                ("partner_id", "in", self.ids),
            ],
            ["partner_id"],
            groupby=["partner_id"],
            lazy=False,
        )
        res = {item["partner_id"][0]: item["__count"] for item in data}

        for record in self:
            record.auth_partner_count = res.get(record.id, 0)

    def _get_auth_partner_for_directory(self, directory):
        return self.sudo().auth_partner_ids.filtered(
            lambda r: r.directory_id == directory
        )
