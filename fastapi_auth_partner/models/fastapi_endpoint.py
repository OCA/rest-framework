# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    directory_id = fields.Many2one("auth.directory")

    is_auth_partner = fields.Boolean(
        compute="_compute_is_auth_partner",
        help="Technical field to know if the auth method is partner",
    )
    public_api_url: str = fields.Char(
        help="The public URL of the API.\n"
        "This URL is used in impersonation to set the cookie on the right API "
        "domain if you use a reverse proxy to serve the API.\n"
        "Defaults to the public_url if not set or the odoo url if not set either."
    )
    # More info in https://github.com/OCA/rest-framework/pull/438/files
    public_url: str = fields.Char(
        help="The public URL of the site.\n"
        "This URL is used for the impersonation final redirect. "
        "And can also be used in the mail template to construct links.\n"
        "Default to the public_api_url if not set or the odoo url if not set either."
    )

    def _get_fastapi_routers(self) -> List[APIRouter]:
        routers = super()._get_fastapi_routers()
        if self.app == "demo" and self.demo_auth_method == "auth_partner":
            routers.append(auth_router)
        return routers

    def _compute_is_auth_partner(self):
        for rec in self:
            rec.is_auth_partner = auth_router in rec._get_fastapi_routers()
