# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import graphene

from odoo import fields, models


def odoo_attr_resolver(attname, default_value, root, info, **args):
    """An attr resolver that is specialized for Odoo recordsets.

    It converts False to None, except for Odoo Boolean fields.
    This is necessary because Odoo null values are often represented
    as False, and graphene would convert a String field with value False
    to "false".

    It converts datetimes to the user timezone.

    It converts a lack of a record to None, if a single record is expected.

    It also raises an error if the attribute is not present, ignoring
    any default value, so as to return if the schema declares a field
    that is not present in the underlying Odoo model.
    """
    value = getattr(root, attname)
    field = root._fields.get(attname)
    if value is False:
        if not isinstance(field, fields.Boolean):
            return None
    elif isinstance(field, fields.Datetime):
        return fields.Datetime.context_timestamp(root, value)
    elif (
        not isinstance(field, fields._RelationalMulti)
        and isinstance(value, models.BaseModel)
        and not value
    ):
        return None
    return value


class OdooObjectType(graphene.ObjectType):
    """A graphene ObjectType with an Odoo aware default resolver."""

    @classmethod
    def __init_subclass_with_meta__(cls, default_resolver=None, **options):
        if default_resolver is None:
            default_resolver = odoo_attr_resolver

        return super(OdooObjectType, cls).__init_subclass_with_meta__(
            default_resolver=default_resolver, **options
        )


def alias(target_name):
    """Return a valid resolver that aliases to another attribute name.

    This lets you work around unsuitable Odoo field names without
    boilerplate and without manually replicating what the default
    resolver does.

    Instead of::

        @staticmethod
        def resolve_child(root, info):
            return root.child_id or None

    Write::

        resolve_child = alias("child_id")
    """

    @classmethod
    def resolve_field(cls, root, info):
        resolver = (
            cls._meta.default_resolver or graphene.types.resolver.get_default_resolver()
        )
        field = cls._meta.fields.get(info.field_name, None)
        default_value = getattr(field, "default_value", None)
        return resolver(target_name, default_value, root, info)

    return resolve_field
