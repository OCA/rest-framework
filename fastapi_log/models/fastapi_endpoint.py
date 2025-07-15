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
        "fastapi.log",
        "endpoint_id",
        string="Logs",
    )

    fastapi_log_count = fields.Integer(
        compute="_compute_fastapi_log_count",
        string="Logs Count",
    )

    @api.depends("fastapi_log_ids")
    def _compute_fastapi_log_count(self):
        data = self.env["fastapi.log"].read_group(
            [("endpoint_id", "in", self.ids)],
            ["endpoint_id"],
            ["endpoint_id"],
        )
        mapped_data = {m["endpoint_id"][0]: m["endpoint_id_count"] for m in data}
        for record in self:
            record.fastapi_log_count = mapped_data.get(record.id, 0)
