# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class WizardPartnerAuthImpersonate(models.TransientModel):
    _name = "wizard.partner.auth.impersonate"
    _description = "Wizard Partner Auth Impersonate"

    fastapi_auth_partner_id = fields.Many2one(
        "fastapi.auth.partner",
        required=True,
    )
    fastapi_auth_directory_id = fields.Many2one(
        "fastapi.auth.directory",
        related="fastapi_auth_partner_id.directory_id",
    )
    fastapi_endpoint_id = fields.Many2one(
        "fastapi.endpoint",
        required=True,
    )

    def action_impersonate(self):
        return self.fastapi_auth_partner_id.with_context(
            fastapi_endpoint_id=self.fastapi_endpoint_id.id
        ).impersonate()
