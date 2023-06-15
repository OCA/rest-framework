# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models

from ..routers.auth_jwt_demo_api import router as auth_jwt_demo_api_router

APP_NAME = "auth_jwt_demo"


class FastapiEndpoint(models.Model):

    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[(APP_NAME, "Auth JWT Demo Endpoint")],
        ondelete={APP_NAME: "cascade"},
    )

    @api.model
    def _get_fastapi_routers(self):
        if self.app == APP_NAME:
            return [auth_jwt_demo_api_router]
        return super()._get_fastapi_routers()
