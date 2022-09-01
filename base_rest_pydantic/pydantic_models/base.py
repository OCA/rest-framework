from extendable_pydantic import ExtendableModelMeta

from odoo.addons.pydantic import utils

from pydantic import BaseModel


class IdAndNameInfo(BaseModel, metaclass=ExtendableModelMeta):
    id: int
    name: str

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class IdRequest(BaseModel, metaclass=ExtendableModelMeta):
    id: int
