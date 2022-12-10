# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel
from pydantic.generics import GenericModel

T = TypeVar("T")


class PagedCollection(GenericModel, Generic[T]):

    total: int
    items: List[T]


class Paging(BaseModel):
    limit: Optional[int]
    offset: Optional[int]
