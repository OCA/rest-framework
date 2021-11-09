import logging

from marshmallow import fields

from odoo import fields as odoo_fields

from odoo.addons.datamodel.fields import NestedModel

_logger = logging.getLogger(__name__)

__all__ = ["convert_field"]


class Binary(fields.Raw):
    def _serialize(self, value, attr, obj, **kwargs):
        res = super()._serialize(value, attr, obj, **kwargs)
        if isinstance(res, bytes):
            res = res.decode("utf-8")
        return res


class FieldConverter:
    def __init__(self, odoo_field):
        self.odoo_field = odoo_field

    def _marshmallow_field_class(self):
        pass

    def _get_kwargs(self):
        kwargs = {
            "required": self.odoo_field.required,
            "allow_none": not self.odoo_field.required,
        }
        if self.odoo_field.readonly:
            kwargs["dump_only"] = True
        return kwargs

    def convert_to_marshmallow(self):
        marshmallow_field_class = self._marshmallow_field_class()
        kwargs = self._get_kwargs()
        return marshmallow_field_class(**kwargs)


class BooleanConverter(FieldConverter):
    def _get_kwargs(self):
        kwargs = super()._get_kwargs()
        kwargs["falsy"] = fields.Boolean.falsy.union({None})
        return kwargs

    def _marshmallow_field_class(self):
        return fields.Boolean


class IntegerConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return fields.Integer


class FloatConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return fields.Float


class StringConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return fields.String


class DateConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return fields.Date


class DatetimeConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return fields.DateTime


class RawConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return fields.Raw


class BinaryConverter(FieldConverter):
    def _marshmallow_field_class(self):
        return Binary


class RelationalConverter(FieldConverter):
    def _get_kwargs(self):
        kwargs = super()._get_kwargs()
        kwargs["many"] = isinstance(
            self.odoo_field, (odoo_fields.One2many, odoo_fields.Many2many)
        )
        kwargs["nested"] = "generic.minimal.serializer"
        kwargs["metadata"] = {"odoo_model": self.odoo_field.comodel_name}
        return kwargs

    def _marshmallow_field_class(self):
        return NestedModel


FIELDS_CONV = {
    odoo_fields.Boolean: BooleanConverter,
    odoo_fields.Integer: IntegerConverter,
    odoo_fields.Id: IntegerConverter,
    odoo_fields.Float: FloatConverter,
    odoo_fields.Monetary: FloatConverter,  # should we use a Decimal instead?
    odoo_fields.Char: StringConverter,
    odoo_fields.Text: StringConverter,
    odoo_fields.Html: StringConverter,
    odoo_fields.Selection: RawConverter,
    odoo_fields.Date: DateConverter,
    odoo_fields.Datetime: DatetimeConverter,
    odoo_fields.Binary: BinaryConverter,
    odoo_fields.Image: BinaryConverter,
    odoo_fields.One2many: RelationalConverter,
    odoo_fields.Many2one: RelationalConverter,
    odoo_fields.Many2many: RelationalConverter,
}


def convert_field(odoo_field):
    field_cls = type(odoo_field)
    if field_cls in FIELDS_CONV:
        return FIELDS_CONV[field_cls](odoo_field).convert_to_marshmallow()
    else:
        _logger.warning(
            "Not implemented: Odoo fields of type {} cannot be "
            "translated into Marshmallow fields".format(field_cls)
        )
