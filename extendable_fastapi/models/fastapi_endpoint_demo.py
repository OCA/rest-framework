# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from fastapi import APIRouter

from ..tests.routers import demo_pydantic_router


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    def _get_fastapi_routers(self) -> list[APIRouter]:
        # Add router defined for tests to the demo app
        routers = super()._get_fastapi_routers()
        if self.app == "demo":
            routers.append(demo_pydantic_router)
        return routers
