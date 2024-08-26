# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
import warnings
from enum import Enum
from typing import Annotated, Generic, TypeVar

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field

T = TypeVar("T")


class PagedCollection(BaseModel, Generic[T]):
    count: Annotated[
        int,
        Field(
            ...,
            description="Count of items into the system.\n "
            "Replaces the total field which is deprecated",
            validation_alias=AliasChoices("count", "total"),
        ),
    ]
    items: list[T]

    @computed_field()
    @property
    def total(self) -> int:
        return self.count

    @total.setter
    def total(self, value: int):
        warnings.warn(
            "The total field is deprecated, please use count instead",
            DeprecationWarning,
            stacklevel=2,
        )
        self.count = value


class Paging(BaseModel):
    limit: int | None
    offset: int | None


#############################################################
# here above you can find models only used for the demo app #
#############################################################
class DemoUserInfo(BaseModel):
    name: str
    display_name: str


class DemoEndpointAppInfo(BaseModel):
    id: int
    name: str
    app: str
    auth_method: str = Field(alias="demo_auth_method")
    root_path: str
    model_config = ConfigDict(from_attributes=True)


class DemoExceptionType(str, Enum):
    user_error = "UserError"
    validation_error = "ValidationError"
    access_error = "AccessError"
    missing_error = "MissingError"
    http_exception = "HTTPException"
    bare_exception = "BareException"
