# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class IrRule(models.Model):
    """Add authenticated_partner_id in record rule evaluation context.

    This come from the env current odoo environment which is
    populated by dependency method authenticated_partner_env or authenticated_partner
    when a route handler depends one of them and is called by the FastAPI service layer.
    """

    _inherit = "ir.rule"

    @api.model
    def _eval_context(self):
        ctx = super()._eval_context()
        if "authenticated_partner_id" in self.env.context:
            ctx["authenticated_partner_id"] = self.env.context[
                "authenticated_partner_id"
            ]
        return ctx

    def _compute_domain_keys(self):
        """Return the list of context keys to use for caching ``_compute_domain``."""
        return super()._compute_domain_keys() + ["authenticated_partner_id"]
