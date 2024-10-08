# Copyright 2024 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta

from odoo import api, fields, models


class WizardAuthPartnerResetPassword(models.TransientModel):
    _name = "wizard.auth.partner.reset.password"
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
    template_id = fields.Many2one(
        "mail.template",
        "Mail Template",
        required=True,
        domain=[("model_id", "=", "auth.partner")],
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

    def action_reset_password(self):
        expiration_delta = None
        if self.delay != "manually":
            duration, key = self.delay.split("-")
            expiration_delta = timedelta(**{key: float(duration)})

        for auth_partner in self.env["auth.partner"].browse(
            self._context["active_ids"]
        ):
            auth_partner.directory_id._send_mail_background(
                self.template_id,
                auth_partner,
                callback_job=auth_partner.delayable()._on_reset_password_sent(),
                token=auth_partner._generate_set_password_token(expiration_delta),
            )
