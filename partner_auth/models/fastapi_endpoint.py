# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import List

from fastapi import APIRouter

from odoo import fields, models

from ..routers.authenticable import auth_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
    )
    demo_auth_method = fields.Selection(
        selection=[
            ("api_key", "Api Key"),
            ("http_basic", "HTTP Basic"),
            ("partner_auth", "Partner Auth"),
        ],
        string="Authenciation method",
    )
    directory_id = fields.Many2one("directory.auth")

    def _get_fastapi_routers(self) -> List[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "demo":
            routers.append(auth_router)
        return routers
