# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FastapiEndpointRouterOption(models.Model):
    _name = "fastapi.endpoint.router.option"
    _description = "FastAPI Endpoint Router Option"

    router_id = fields.Many2one("fastapi.router", required=True)
    endpoint_id = fields.Many2one("fastapi.endpoint", required=True)
    prefix = fields.Char()

    auth_method = fields.Selection(
        selection=lambda self: self.env["fastapi.endpoint"]
        ._fields["dynamic_auth_method"]
        .selection,
        string="Auth method for this router",
    )
    specific_partner_id = fields.Many2one(
        "res.partner",
        string="Specific Partner",
        help="The partner to use for the specific partner demo.",
    )

    _sql_constraints = [
        (
            "name_router_endpoint_unique",
            "unique(router_id, endpoint_id)",
            "Option already exists",
        )
    ]
