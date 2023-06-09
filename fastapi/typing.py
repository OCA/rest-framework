# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from typing import Optional

from odoo import fields

from pydantic import errors
from pydantic.fields import ModelField

from .context import odoo_env_ctx


class OdooFieldSelection(str):
    """
    A type to represent a selection field from odoo.

    This type allows you to define a pydantic field with the same constraints
    as a selection field from odoo.
    The type is a string and the possible values are the ones defined in the
    selection field from odoo. When used, the validation will check that the
    value is one of the possible values from the selection field. It will also
    extend the documentation of the field with the possible values and a description
    based on the selections (value: Title) and the help of the field.

    Usage:

    To work, the type needs to be used with the `Field` class from pydantic. The
    `odoo_model_name` and `odoo_field_name` need to be specified in the `extra`
    attribute of the field. The `odoo_model_name` is the name of the odoo model
    where the field is defined and the `odoo_field_name` is the name of the field
    in the odoo model.

    .. code-block:: python


        from odoo.addons.pydantic.typing import OdooFieldSelection
        from pydantic import BaseModel, Field

        class PartnerModel(BaseModel):
            type: OdooFieldSelection = Field(
                odoo_model_name="res.partner", odoo_field_name="type")

    """

    @classmethod
    def _get_odoo_field(cls, field: ModelField) -> fields.Selection:
        """
        Get the odoo field from the pydantic field info
        """
        model_name = field.field_info.extra["odoo_model_name"]
        field_name = field.field_info.extra["odoo_field_name"]
        env = odoo_env_ctx.get()
        return env[model_name]._fields[field_name]

    @classmethod
    def _get_selection(cls, field: ModelField) -> list[str]:
        """
        Get the list of possible values from the odoo field specified
        in the pydantic field info.
        """
        env = odoo_env_ctx.get()
        odoo_field = cls._get_odoo_field(field)
        return odoo_field.get_values(env)

    @classmethod
    def _get_description(cls, field: Optional[ModelField]) -> str:
        """
        Get the description to from the odoo field specified in the pydantic
        field info. The description is a string with the possible values
        of the field and the help of the field if any is available.

        The description is used to complete the documentation of the field
        into the openapi schema.
        """
        if field:
            odoo_field = cls._get_odoo_field(field)
            env = odoo_env_ctx.get()
            description_selection = odoo_field._description_selection(env)
            description_selection = [
                f"* {key}: {title}" for (key, title) in description_selection
            ]
            description_help = odoo_field._description_help(odoo_env_ctx.get())
            description = "\n".join(description_selection)
            if description_help:
                description += "\n\n" + description_help
            return description
        return ""

    @classmethod
    def validate(cls, value, field: ModelField):
        """
        Validate the value against the possible values of the odoo field.

        This method is called by pydantic when a value is assigned to the
        pydantic field.
        """
        selection = cls._get_selection(field)
        if value not in selection:
            raise errors.EnumMemberError(enum_values=selection)
        return cls(value)

    # Pydantic method hooks

    @classmethod
    def __get_validators__(cls):
        """
        Method hook called by pydantic to get the validators to use to validate
        the field.
        """
        yield cls.validate

    @classmethod
    def __modify_schema__(cls, field_schema, field: Optional[ModelField]):
        """
        Modify the schema of the pydantic field to include the possible values
        and the description of the odoo field into the OpenAPI schema.
        """
        if field:
            selection = cls._get_selection(field)
            field_schema["enum"] = selection
            field_schema.pop("odoo_model_name", None)
            field_schema.pop("odoo_field_name", None)
            if not field_schema.get("desciption"):
                cls._get_odoo_field(field)
                description = cls._get_description(field)
                if description:
                    field_schema["description"] = description
