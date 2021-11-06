# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import collections
from typing import DefaultDict, List, TypeVar, Union

import pydantic
from pydantic.utils import ClassAttribute

from . import utils

ModelType = TypeVar("Model", bound="BaseModel")


class BaseModel(pydantic.BaseModel):
    _name: str = None
    _inherit: Union[List[str], str] = None

    _pydantic_classes_by_module: DefaultDict[
        str, List[ModelType]
    ] = collections.defaultdict(list)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if cls != BaseModel:
            cls.__normalize__definition__()
            cls.__register__()

    @classmethod
    def __normalize__definition__(cls):
        """Normalize class definition

        Compute the module name
        Compute and validate the model name if class is a subclass
        of another BaseModel;
        Ensure that _inherit is a list
        """
        parents = cls._inherit
        if isinstance(parents, str):
            parents = [parents]
        elif parents is None:
            parents = []
        name = cls._name or (parents[0] if len(parents) == 1 else None)
        if not name:
            raise TypeError(f"Extended pydantic class {cls} must have a name")
        cls._name = ClassAttribute("_module", name)
        cls._module = ClassAttribute("_module", utils._get_addon_name(cls.__module__))
        cls.__config__.title = name
        # all BaseModels except 'base' implicitly inherit from 'base'
        if name != "base":
            parents = list(parents) + ["base"]
        cls._inherit = ClassAttribute("_inherit", parents)

    @classmethod
    def __register__(cls):
        """Register the class into the list of classes defined by the module"""
        if "tests" not in cls.__module__.split(":"):
            cls._pydantic_classes_by_module[cls._module].append(cls)


class Base(BaseModel):
    """This is the base pydantic BaseModel for every BaseModels

    It is implicitely inherited by all BaseModels.

    All your base are belong to us
    """

    _name = "base"


class OdooOrmMode(BaseModel):
    """Generic model that can be used to instantiate pydantis model from
    odoo models

    Usage:

     .. code-block:: python

         class UserInfo(models.BaseModel):
            _name = "user"
            _inherit = "odoo_orm_mode"
            name: str
            groups: List["group"] = pydantic.Field(alias="groups_id")


        class Group(models.BaseModel):
            _name="group"
            _inherit = "odoo_orm_mode"
            name: str

        user = self.env.user
        UserInfoCls = self.env.pydantic_registry["user"]
        user_info = UserInfoCls.from_orm(user)

    """

    _name = "odoo_orm_mode"

    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter
