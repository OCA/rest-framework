# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    log_requests = fields.Boolean(
        help="Log requests in database.",
    )

    fastapi_log_ids = fields.One2many(
        comodel_name="api.log",
        inverse_name="fastapi_endpoint_id",
        string="Logs",
    )

    fastapi_log_count = fields.Integer(
        compute="_compute_fastapi_log_count",
        string="Logs Count",
    )

    @api.depends("fastapi_log_ids")
    def _compute_fastapi_log_count(self):
        groups = self.env["api.log"].read_group(
            [("fastapi_endpoint_id", "in", self.ids)],
            ["fastapi_endpoint_id"],
            ["fastapi_endpoint_id"],
        )
        mapped_data = {
            g["fastapi_endpoint_id"][0]: g["fastapi_endpoint_id_count"] for g in groups
        }
        for endpoint in self:
            endpoint.fastapi_log_count = mapped_data.get(endpoint.id, 0)
