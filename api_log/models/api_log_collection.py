# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class APILogCollection(models.AbstractModel):
    _name = "api.log_collection.mixin"
    _description = "Collection of API logs"

    log_requests = fields.Boolean(
        help="Log requests in database.",
    )

    log_ids = fields.One2many(
        comodel_name="api.log",
        compute="_compute_log_ids",
        string="Logs",
    )

    def _get_logs_domain(self):
        """Domain to find the logs in `self`."""
        return [
            ("collection_model", "=", self._name),
            ("collection_id", "in", self.ids),
        ]

    def _compute_log_ids(self):
        all_logs = self.env["api.log"].search_read(
            domain=self._get_logs_domain(),
            fields=[
                "collection_id",
            ],
            load=None,
        )
        log_ids_by_collection_id = {}
        for log in all_logs:
            log_ids_by_collection_id.setdefault(log["collection_id"], []).append(
                log["id"]
            )

        for collection in self:
            collection.log_ids = log_ids_by_collection_id.get(collection.id)

    def action_logs(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "api.log",
            "name": "Logs",
            "view_type": "form",
            "view_mode": "list,form",
            "target": "current",
            "domain": self._get_logs_domain(),
            "context": dict(self.env.context),
        }
