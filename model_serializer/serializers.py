from marshmallow import fields

from .core import ModelSerializer


class GenericAbstractSerializer(ModelSerializer):
    _name = "generic.abstract.serializer"
    _model = "base"
    _register = False

    def __init__(self, *args, **kwargs):
        if kwargs.get("_model"):
            self._model = kwargs.pop("_model")
        super().__init__(*args, **kwargs)


class GenericMinimalSerializer(GenericAbstractSerializer):
    _name = "generic.minimal.serializer"
    _model_fields = ["id", "display_name"]

    id = fields.Integer(dump_only=True)
    display_name = fields.String(dump_only=True)

    def to_recordset(self):
        return self.get_odoo_record()
