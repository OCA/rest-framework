# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from odoo import api, models


class IrAccess(models.Model):
    """Add authenticated_partner_id in record rule/access evaluation context."""

    _inherit = "ir.access"

    @api.model
    def _eval_context(self):
        ctx = super()._eval_context()
        ctx["authenticated_partner_id"] = self.env.context.get(
            "authenticated_partner_id", False
        )
        return ctx

    def _get_access_context(self):
        yield from super()._get_access_context()
        yield self.env.context.get("authenticated_partner_id")
