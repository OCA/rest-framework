# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).
from typing import Generic, TypeVar

from extendable_pydantic import ExtendableBaseModel

# User models


class User(ExtendableBaseModel, revalidate_instances="always"):
    """
    We MUST set revalidate_instances="always" to be sure that FastAPI validates
    responses of this model type.
    """

    name: str

    @classmethod
    def from_user(cls, user):
        return cls.model_construct(name=user.name)


class ExtendedUser(User, extends=True):
    address: str

    @classmethod
    def from_user(cls, user):
        res = super().from_user(user)
        if user.street or user.city:
            # Dummy address construction
            res.address = (user.street or "") + (user.city or "")
        return res


class PrivateUser(User):
    password: str

    @classmethod
    def from_user(cls, user):
        res = super().from_user(user)
        res.password = user.password
        return res


_T = TypeVar("_T")


class SearchResponse(ExtendableBaseModel, Generic[_T]):
    total: int
    items: list[_T]


class UserSearchResponse(SearchResponse[User]):
    """We declare the generic type of the items of the list as User
    which is the base model of the extended. When used, it should be resolved
    to ExtendedUser, but items of PrivateUser class must stay private and not be returned"""


# Customer models: same as above but with extra="forbid"


class Customer(ExtendableBaseModel, revalidate_instances="always", extra="forbid"):
    """
    Same hierarchy as User models, but with an extra config parameter:
    forbid extra fields.
    """

    name: str

    @classmethod
    def from_customer(cls, customer):
        return cls.model_construct(name=customer.name)


class ExtendedCustomer(Customer, extends=True):
    address: str

    @classmethod
    def from_customer(cls, customer):
        res = super().from_customer(customer)
        if customer.street or customer.city:
            # Dummy address construction
            res.address = (customer.street or "") + (customer.city or "")
        return res


class PrivateCustomer(Customer):
    password: str

    @classmethod
    def from_customer(cls, customer):
        res = super().from_customer(customer)
        res.password = customer.password
        return res
