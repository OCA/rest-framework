# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from typing import Any

from odoo import fields, models

from pydantic.utils import GetterDict


class GenericOdooGetter(GetterDict):
    """A generic GetterDict for Odoo models

    The getter take care of casting one2many and many2many
    field values to python list to allow the from_orm method from
    pydantic class to work on odoo models. This getter is to specify
    into the pydantic config.

    Usage:

     .. code-block:: python

        import pydantic
        from odoo.addons.pydantic import models, utils

        class Group(models.BaseModel):
            name: str

            class Config:
                orm_mode = True
                getter_dict = utils.GenericOdooGetter

        class UserInfo(models.BaseModel):
            name: str
            groups: List[Group] = pydantic.Field(alias="groups_id")

            class Config:
                orm_mode = True
                getter_dict = utils.GenericOdooGetter

        user = self.env.user
        user_info = UserInfo.from_orm(user)

    To avoid having to repeat the specific configuration required for the
    `from_orm` method into each pydantic model, "odoo_orm_mode" can be used
     as parent via the `_inherit` attribute

    """

    def get(self, key: Any, default: Any = None) -> Any:
        res = getattr(self._obj, key, default)
        if isinstance(self._obj, models.BaseModel) and key in self._obj._fields:
            field = self._obj._fields[key]
            if res is False and field.type != "boolean":
                return None
            if field.type == "date" and not res:
                return None
            if field.type == "datetime":
                if not res:
                    return None
                # Get the timestamp converted to the client's timezone.
                # This call also add the tzinfo into the datetime object
                return fields.Datetime.context_timestamp(self._obj, res)
            if field.type == "many2one" and not res:
                return None
            if field.type in ["one2many", "many2many"]:
                return list(res)
        return res
