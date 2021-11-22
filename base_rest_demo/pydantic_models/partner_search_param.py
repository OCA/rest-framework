# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.pydantic import models


class PartnerSearchParam(models.BaseModel):

    id: int = None
    name: str = None
