# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from typing import List

from odoo import fields, models
from odoo.api import Environment

from fastapi import APIRouter, Depends

from ..depends import odoo_env


class FastapiEndpoint(models.Model):

    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("demo", "Demo Endpoint")], ondelete={"demo": "cascade"}
    )

    def _get_fastapi_routers(self) -> List[APIRouter]:
        if self.app == "demo":
            return [demo_api_router]
        return super()._get_fastapi_routers()


demo_api_router = APIRouter()


@demo_api_router.get("/")
async def hello_word():
    """Hello World!"""
    return {"Hello": "World"}


@demo_api_router.get("/contacts")
async def count_partners(env: Environment = Depends(odoo_env)):  # noqa: B008
    """Returns the number of contacts into the database"""
    count = env["res.partner"].sudo().search_count([])
    return {"count": count}
