# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from enum import Enum
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field
from pydantic.generics import GenericModel

T = TypeVar("T")


class PagedCollection(GenericModel, Generic[T]):

    total: int
    items: List[T]


class Paging(BaseModel):
    limit: Optional[int]
    offset: Optional[int]


#############################################################
# here above you can find models only used for the demo app #
#############################################################
class DemoUserInfo(BaseModel):
    name: str
    display_name: str


class DemoEndpointAppInfo(BaseModel):
    id: str
    name: str
    app: str
    auth_method: str = Field(alias="demo_auth_method")
    root_path: str

    class Config:
        orm_mode = True


class DemoExceptionType(str, Enum):
    user_error = "UserError"
    validation_error = "ValidationError"
    access_error = "AccessError"
    missing_error = "MissingError"
    http_exception = "HTTPException"
    bare_exception = "BareException"
