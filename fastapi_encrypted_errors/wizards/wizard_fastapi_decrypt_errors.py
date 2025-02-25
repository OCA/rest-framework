# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import traceback

from odoo import fields, models


class WizardFastapiDecryptErrors(models.TransientModel):
    _name = "wizard.fastapi.decrypt.errors"
    _description = "Wizard to decrypt FastAPI errors"

    error = fields.Text(required=True)
    fastapi_endpoint_id = fields.Many2one(
        "fastapi.endpoint",
        string="FastAPI Endpoint",
        required=True,
        default=lambda self: self.env["fastapi.endpoint"].search([], limit=1),
    )
    decrypted_error = fields.Text(readonly=True)

    def action_decrypt_error(self):
        self.ensure_one()
        try:
            error = self.fastapi_endpoint_id._decrypt_error(self.error.encode("utf-8"))
        except Exception:
            self.decrypted_error = (
                "Error while decrypting error: \n\n" + traceback.format_exc()
            )
        else:
            self.decrypted_error = error

        return {
            "type": "ir.actions.act_window",
            "res_model": "wizard.fastapi.decrypt.errors",
            "view_mode": "form",
            "view_type": "form",
            "res_id": self.id,
            "target": "new",
        }
