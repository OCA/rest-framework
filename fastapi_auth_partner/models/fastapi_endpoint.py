# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import List

from odoo import fields, models

from fastapi import APIRouter

from ..routers.auth import auth_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
    )
    demo_auth_method = fields.Selection(
        selection_add=[
            ("auth_partner", "Partner Auth"),
        ],
        string="Authentication method",
    )
    directory_id = fields.Many2one("fastapi.auth.directory")

    is_partner_auth = fields.Boolean(
        compute="_compute_is_partner_auth",
        help="Technical field to know if the auth method is partner",
    )

    def _get_fastapi_routers(self) -> List[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "demo" and self.demo_auth_method == "auth_partner":
            routers.append(auth_router)
        return routers

    def _compute_is_partner_auth(self):
        for rec in self:
            rec.is_partner_auth = auth_router in rec._get_fastapi_routers()
