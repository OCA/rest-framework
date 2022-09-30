# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import List

from extendable_pydantic import ExtendableModelMeta

from odoo.addons.base_rest_pydantic.pydantic_models.base import IdAndNameInfo
from odoo.addons.pydantic import utils

from pydantic import BaseModel, Field


class AttachmentRequest(BaseModel, metaclass=ExtendableModelMeta):
    name: str = None


class AttachmentInfo(BaseModel, metaclass=ExtendableModelMeta):
    id: int
    name: str

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class AttachableInfo(BaseModel, metaclass=ExtendableModelMeta):
    attachments: List[IdAndNameInfo] = Field([], alias="attachment_ids")

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
