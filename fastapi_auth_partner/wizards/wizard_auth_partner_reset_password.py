# Copyright 2024 Akretion (https://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class WizardAuthPartnerResetPassword(models.TransientModel):
    _inherit = "wizard.auth.partner.reset.password"

    fastapi_endpoint_id = fields.Many2one(
        "fastapi.endpoint",
    )

    def action_reset_password(self):
        if self.fastapi_endpoint_id:
            self = self.with_context(_fastapi_endpoint_id=self.fastapi_endpoint_id.id)
        return super(WizardAuthPartnerResetPassword, self).action_reset_password()
