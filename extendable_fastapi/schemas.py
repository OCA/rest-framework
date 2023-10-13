from typing import Annotated, Generic, TypeVar

from extendable_pydantic import StrictExtendableBaseModel

from pydantic import Field

T = TypeVar("T")


class PagedCollection(StrictExtendableBaseModel, Generic[T]):
    """A paged collection of items"""

    # This is a generic model. The type of the items is defined by the generic type T.
    # It provides you a common way to return a paged collection of items of
    # extendable models. It's based on the StrictExtendableBaseModel to ensure
    # a strict validation when used within the odoo fastapi framework.

    count: Annotated[int, Field(..., description="The count of items into the system")]
    items: list[T]
