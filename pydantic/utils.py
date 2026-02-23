# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from typing import Any

from odoo import fields, models

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
    * using int type on many2one return the foreign key id
      (not the odoo record)
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    @classmethod
    def model_validate(
        cls,
        obj: Any,
        *,
        context: Any | None = None,
        **kwargs,
    ):
        if context is None:
            context = {}

        if "odoo_records" not in context:
            context["odoo_records"] = {}

        return super().model_validate(
            obj,
            context=context,
            **kwargs,
        )

    @field_validator("*", mode="before")
    @classmethod
    def odoo_validator_before(cls, value: Any, info: ValidationInfo):
        odoo_record = info.context and info.context.get("odoo_records").get(
            info.config.get("title")
        )
        if odoo_record is not None:
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
        if isinstance(info.context, dict):
            info.context["odoo_records"][info.config.get("title")] = (
                data if isinstance(data, models.BaseModel) else None
            )
        return data
