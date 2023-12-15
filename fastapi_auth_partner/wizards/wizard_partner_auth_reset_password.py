# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from odoo import api, fields, models


class WizardPartnerAuthResetPassword(models.Model):
    _name = "wizard.partner.auth.reset.password"
    _description = "Wizard Partner Auth Reset Password"

    delay = fields.Selection(
        [
            ("manually", "Manually"),
            ("6-hours", "6 Hours"),
            ("2-days", "2-days"),
            ("7-days", "7 Days"),
            ("14-days", "14 Days"),
        ],
        default="6-hours",
        required=True,
    )
    partner_ids = fields.Many2many(comodel_name="shopinvader.partner")
    template_id = fields.Many2one(
        "mail.template",
        "Mail Template",
        required=True,
        domain=[("model_id", "=", "fastapi.auth.partner")],
    )
    date_validity = fields.Datetime(
        compute="_compute_date_validity", store=True, readonly=False
    )

    @api.depends("delay")
    def _compute_date_validity(self):
        for record in self:
            if record.delay != "manually":
                duration, key = record.delay.split("-")
                record.date_validity = datetime.now() + timedelta(
                    **{key: float(duration)}
                )

    def confirm(self):
        for auth_partner in self.env["fastapi.auth.partner"].browse(
            self._context["active_ids"]
        ):
            auth_partner.with_delay().send_reset_password(
                self.template_id, force_expiration=self.date_validity
            )
