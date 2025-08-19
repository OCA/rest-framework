# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

try:
    import altcha
    from altcha import verify_solution
except ImportError:
    altcha = None


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    captcha_type = fields.Selection(
        selection_add=[
            ("altcha_local", "Altcha (Local)"),
        ],
    )

    def validate_captcha(self, captcha_response):
        """Validate the captcha response."""
        super().validate_captcha(captcha_response)
        secret_key = self.captcha_secret_key
        if self.captcha_type == "altcha_local":
            if not altcha:
                raise UserError(_("Altcha library is not installed."))
            return self._validate_altcha_local(captcha_response, secret_key)

    def _validate_altcha_local(self, captcha_response, secret_key):
        """Validate the altcha"""

        try:
            # Verify the solution
            verified, err = verify_solution(captcha_response, secret_key, True)
            if not verified:
                raise AccessError(
                    _("Altcha validation failed: %(error)s") % {"error": err}
                )

            return
        except Exception as e:
            raise ValidationError(
                _("Failed to process Altcha payload: %(error)s") % {"error": str(e)}
            ) from e
