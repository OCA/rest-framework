# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from extendable_pydantic import ExtendableModelMeta

from odoo.addons.pydantic import utils

from pydantic import BaseModel


class NaiveOrmModel(BaseModel, metaclass=ExtendableModelMeta):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
