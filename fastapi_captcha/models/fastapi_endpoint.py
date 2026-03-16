# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from typing import Annotated

import requests
from starlette.middleware import Middleware

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from fastapi import Depends, Header

from ..captcha_middleware import CaptchaMiddleware


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    use_captcha = fields.Boolean(
        help="If checked, this endpoint will be protected by a captcha",
    )

    captcha_type = fields.Selection(
        [
            ("recaptcha", "Recaptcha"),
            ("hcaptcha", "Hcaptcha"),
            ("altcha", "Altcha"),
        ],
        help="Type of captcha to use for this endpoint",
    )

    captcha_secret_key = fields.Char(
        help="Secret key to use for the captcha validation",
        groups="base.group_system",
    )

    captcha_routes_regex = fields.Char(
        help="Regexes to match against routes url that should be protected "
        "by this captcha, comma separated. If empty, all routes will be protected",
    )

    captcha_minimum_score = fields.Float(
        default=0.5,
        help="Minimum score to accept the captcha if a score is provided by the "
        "captcha service.",
    )

    captcha_custom_verify_url = fields.Char(
        help="Custom URL to use for the captcha verification",
    )

    @property
    def _server_env_fields(self):
        fields = getattr(super(), "_server_env_fields", None) or {}
        fields["captcha_secret_key"] = {}
        return fields

    @api.constrains("captcha_routes_regex")
    def _check_captcha_routes_regex(self):
        """Check that the captcha routes regex is valid"""
        for record in self:
            if record.captcha_routes_regex:
                for rex in record.captcha_routes_regex.split(","):
                    rex = rex.strip()
                    if not rex:
                        continue
                    # Check that the regex is valid
                    try:
                        re.compile(rex)
                    except re.error as e:
                        raise ValidationError(
                            self.env._(
                                "Invalid regex for captcha routes: %(regex)s "
                                "(error: %(error)s)"
                            )
                            % {
                                "regex": rex,
                                "error": str(e),
                            }
                        ) from e

    def _get_fastapi_app_middlewares(self):
        # Add the captcha middleware to the list of middlewares if enabled
        middlewares = super()._get_fastapi_app_middlewares()
        if self.use_captcha:
            middlewares.append(
                Middleware(
                    CaptchaMiddleware,
                    endpoint_id=self.id,
                    root_path=self.root_path,
                    routes_regex=[
                        re.compile(rex) for rex in self.captcha_routes_regex.split(",")
                    ]
                    if self.captcha_routes_regex
                    else None,
                )
            )
        return middlewares

    def _get_fastapi_app_dependencies(self):
        # Add the captcha header to the list of dependencies
        dependencies = super()._get_fastapi_app_dependencies()
        if self.use_captcha:
            dependencies.append(Depends(captcha_token))

        return dependencies

    def validate_captcha(self, captcha_response):
        """Validate the captcha response."""
        secret_key = self.captcha_secret_key
        if not secret_key:
            raise UserError(self.env._("No secret key found for this endpoint"))

        if self.captcha_type == "recaptcha":
            return self._validate_recaptcha(captcha_response, secret_key)
        elif self.captcha_type == "hcaptcha":
            return self._validate_hcaptcha(captcha_response, secret_key)
        elif self.captcha_type == "altcha":
            return self._validate_altcha(captcha_response, secret_key)

    def _validate_recaptcha(self, captcha_response, secret_key):
        """Validate the recaptcha response"""
        data = {
            "secret": secret_key,
            "response": captcha_response,
        }
        response = requests.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data=data,
            timeout=10,
        )
        result = response.json()
        success = result.get("success", False)
        if not success:
            error_codes = result.get("error-codes", ["?"])
            raise AccessError(
                self.env._("Recaptcha validation failed: %s") % ", ".join(error_codes)
            )
        score = result.get("score", 1)
        if score < self.captcha_minimum_score:
            raise AccessError(
                self.env._(
                    "Recaptcha validation failed: score %(score)s < %(min_score)s"
                )
                % {
                    "score": score,
                    "min_score": self.captcha_minimum_score,
                }
            )

    def _validate_hcaptcha(self, captcha_response, secret_key):
        """Validate the hcaptcha response"""

        data = {
            "secret": secret_key,
            "response": captcha_response,
        }
        response = requests.post(
            "https://api.hcaptcha.com/siteverify", data=data, timeout=10
        )
        result = response.json()
        success = result.get("success", False)
        if not success:
            error_codes = result.get("error-codes", ["?"])
            raise AccessError(
                self.env._("Hcaptcha validation failed: %s") % ", ".join(error_codes)
            )
        score = result.get("score", 1)
        if score < self.captcha_minimum_score:
            raise AccessError(
                self.env._(
                    "Hcaptcha validation failed: score %(score)s < %(min_score)s "
                    "(%(reason)s)"
                )
                % {
                    "score": score,
                    "min_score": self.captcha_minimum_score,
                    "reason": result.get("score_reason", ""),
                }
            )

    def _validate_altcha(self, captcha_response, secret_key):
        """Validate the altcha response"""
        data = {
            "apiKey": secret_key,
            "payload": captcha_response,
        }
        url = (
            self.captcha_custom_verify_url
            or "https://eu.altcha.org/api/v1/challenge/verify"
        )
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        success = result.get("verified", False)
        if not success:
            error = result.get("error", "?")
            raise AccessError(
                self.env._("Altcha (%(url)s) validation failed: %(error)s")
                % {"url": url, "error": error}
            )

    @api.model
    def _fastapi_app_fields(self):
        # We need to reload fastapi app when we change these captcha fields
        fields = super()._fastapi_app_fields()
        return [
            "use_captcha",
            "captcha_routes_regex",
        ] + fields


def captcha_token(
    captcha_token: Annotated[
        str | None,
        Header(
            alias="X-Captcha-Token",
            description="The X-Captcha-Token header is used to specify the captcha ",
        ),
    ] = None,
) -> str:
    return captcha_token
