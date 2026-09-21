# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import fields, models


class AltchaToken(models.Model):
    _name = "altcha.token"
    _description = "Altcha Token"

    endpoint_id = fields.Many2one("fastapi.endpoint")
    token = fields.Char()

    def _clean(self):
        endpoints = self.env["fastapi.endpoint"].search([])
        for endpoint in endpoints:
            self.search(
                [
                    ("endpoint_id", "=", endpoint.id),
                    (
                        "create_date",
                        "<",
                        fields.Datetime.now()
                        - timedelta(minutes=endpoint.altcha_validity_period),
                    ),
                ]
            ).unlink()

    def _check_token(self, endpoint, token):
        record = self.search([("endpoint_id", "=", endpoint.id), ("token", "=", token)])
        if not record:
            self.create({"endpoint_id": endpoint.id, "token": token})
            return True
