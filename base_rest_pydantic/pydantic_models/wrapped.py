# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from typing import Generic, List, TypeVar

from pydantic.generics import GenericModel

DataT = TypeVar("DataT")


class WrappedList(GenericModel, Generic[DataT]):
    data: List[DataT]
