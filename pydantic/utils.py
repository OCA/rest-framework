# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from typing import Any

from packaging.version import Version

from odoo import fields, models

from pydantic import __version__ as pydantic_version

PYDANTIC_V2: bool = Version(pydantic_version) >= Version("2.0")


if PYDANTIC_V2:
    from pydantic import (
        BaseModel,
        ConfigDict,
        ValidationInfo,
        field_validator,
        model_validator,
    )

    class PydanticOdooBaseModel(BaseModel):
        """Pydantic BaseModel for odoo record

        This aims to help to serialize Odoo record
        improving behavior like previous version:

        * Avoid False value on non boolean fields
        * Convert Datetime to Datetime timezone aware
        * if manyone

        """

        model_config = ConfigDict(
            from_attributes=True,
        )

        @field_validator("*", mode="before")
        @classmethod
        def odoo_validator_before(cls, value: Any, info: ValidationInfo):
            odoo_record = info.config.get("odoo_record")
            if odoo_record:
                if info.field_name in odoo_record._fields:
                    field = odoo_record._fields[info.field_name]
                    if value is False and field.type != "boolean":
                        return None
                    if field.type == "datetime":
                        # Get the timestamp converted to the client's timezone.
                        # This call also add the tzinfo into the datetime object
                        return fields.Datetime.context_timestamp(odoo_record, value)
                    if field.type == "many2one":
                        if not value:
                            return None
                        if issubclass(cls.__annotations__.get(info.field_name), int):
                            # if field typing is an integer we return the .id
                            # (not the odoo record)
                            return value.id
            return value

        @model_validator(mode="before")
        @classmethod
        def odoo_model_validator(cls, data: Any, info: ValidationInfo) -> Any:
            info.config["odoo_record"] = (
                data if isinstance(data, models.BaseModel) else None
            )
            return data

else:
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
                    # PV: tests prove that this is useless, I'm wondering if
                    # there is case where data can be Falsy but not False?
                    # keeping to avoid regressions
                    return None
                if field.type == "datetime":
                    if not res:
                        # I'm wondering if there is case where data can be
                        # Falsy but not False?
                        # keeping to avoid regressions
                        return None
                    # Get the timestamp converted to the client's timezone.
                    # This call also add the tzinfo into the datetime object
                    return fields.Datetime.context_timestamp(self._obj, res)
                if field.type == "many2one" and not res:
                    return None
                if field.type in ["one2many", "many2many"]:
                    return list(res)
            return res
