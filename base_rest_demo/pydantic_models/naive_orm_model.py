# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from extendable_pydantic import ExtendableModelMeta

from pydantic import BaseModel, ConfigDict


class NaiveOrmModel(BaseModel, metaclass=ExtendableModelMeta):
    model_config: ConfigDict = ConfigDict(from_attributes=True)
