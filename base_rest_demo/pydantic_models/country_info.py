# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from .naive_orm_model import NaiveOrmModel


class CountryInfo(NaiveOrmModel):

    id: int
    name: str
