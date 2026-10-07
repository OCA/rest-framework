# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models
from odoo.exceptions import AccessError, UserError

try:
    import altcha
    from altcha import verify_solution, verify_solution_v1
except ImportError:
    altcha = None


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    captcha_type = fields.Selection(
        selection_add=[
            ("altcha_local", "Altcha (Local)"),
        ],
    )

    altcha_validity_period = fields.Integer(
        default=5,
        help="Validity period for the altcha in minutes",
    )

    def validate_captcha(self, captcha_response):
        """Validate the captcha response."""
        super().validate_captcha(captcha_response)
        secret_key = self.captcha_secret_key
        if self.captcha_type == "altcha_local":
            if not altcha:
                raise UserError(self.env._("Altcha library is not installed."))
            return self._validate_altcha_local(captcha_response, secret_key)

    def _validate_altcha_local(self, captcha_response, secret_key):
        """Validate the altcha"""

        try:
            # Verify the solution
            result = verify_solution(captcha_response, secret_key)
            if not result.verified:
                # Check using legacy verification for backward compatibility
                # with old challenges
                verified, err = verify_solution_v1(captcha_response, secret_key, True)
                if not verified:
                    raise AccessError(
                        self.env._("Altcha validation failed: %(error)s")
                        % {"error": "\n--\n".join(e for e in (err, result.error) if e)}
                    )
            if not self.env["altcha.token"]._check_token(self, captcha_response):
                raise AccessError(
                    self.env._("Altcha validation failed: Token already used")
                )

        except Exception as e:
            raise AccessError(
                self.env._("Failed to process Altcha payload: %(error)s")
                % {"error": str(e)}
            ) from e
