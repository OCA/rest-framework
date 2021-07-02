from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.datamodel.core import Datamodel, MetaDatamodel, _datamodel_databases

from .field_converter import convert_field


def to_camelcase(txt):
    tokens = [t.title() for t in txt.split("._")]
    return "".join(tokens)


class DatamodelBuilder(models.AbstractModel):
    _inherit = "datamodel.builder"

    def load_datamodels(self, module, datamodels_registry=None):
        super().load_datamodels(module, datamodels_registry=datamodels_registry)
        datamodels_registry = (
            datamodels_registry or _datamodel_databases[self.env.cr.dbname]
        )
        for datamodel_class in MetaDatamodel._modules_datamodels[module]:
            self._extend_model_serializer(datamodel_class, datamodels_registry)

    def _build_default_nested_class(self, marshmallow_field, odoo_field, registry):
        """If `marshmallow_field` is a nested datamodel (relational field), we build
        a default model_serializer class (if it does not exist yet).

        The default model_serializer simply returns the `display_name` and the `id`
        """
        nested_name = getattr(marshmallow_field, "datamodel_name", None)
        if nested_name and nested_name not in registry:
            nested_attrs = {
                "_name": nested_name,
                "_model": odoo_field.comodel_name,
                "_model_fields": ["id", "display_name"],
            }
            nested_class = MetaDatamodel(
                to_camelcase(nested_name), (ModelSerializer,), nested_attrs
            )
            registry[nested_name] = nested_class
            nested_class._build_datamodel(registry)
            self._extend_model_serializer(nested_class, registry)

    def _extend_model_serializer(self, datamodel_class, registry):
        """Extend the datamodel_class with the fields declared in `_model_fields`"""
        if issubclass(datamodel_class, ModelSerializer):
            attrs = {
                "_inherit": datamodel_class._name,
                "_model_fields": datamodel_class._model_fields,
                "_model": datamodel_class._model,
            }
            bases = (ModelSerializer,)
            name = datamodel_class.__name__ + "Child"
            odoo_model = self.env[datamodel_class._model]
            for field_name in datamodel_class._model_fields:
                if not hasattr(datamodel_class, field_name):
                    odoo_field = odoo_model._fields[field_name]
                    marshmallow_field = convert_field(odoo_field)
                    if marshmallow_field:
                        attrs[field_name] = marshmallow_field
                        self._build_default_nested_class(
                            marshmallow_field, odoo_field, registry
                        )

            parent_class = registry[datamodel_class._name]
            if getattr(parent_class, "_model_fields", None):
                _model_fields = list(
                    set(attrs["_model_fields"] + parent_class._model_fields)
                )
                attrs["_model_fields"] = _model_fields
            new_class = MetaDatamodel(name, bases, attrs)
            new_class._build_datamodel(registry)


class MetaModelSerializer(MetaDatamodel):
    def __init__(self, name, bases, attrs):
        register = attrs.get("_register")
        if register and not (attrs.get("_model") and attrs.get("_model_fields")):
            raise ValidationError(
                _(
                    "Model Serializers require '_model' and '_model_fields' "
                    "attributes to be defined"
                )
            )
        super(MetaModelSerializer, self).__init__(name, bases, attrs)


class ModelSerializer(Datamodel, metaclass=MetaModelSerializer):
    _inherit = "base"
    _register = False
    _model = None
    _model_fields = []

    @classmethod
    def from_recordset(cls, recordset, many=False):
        """Transform a recordset into a (list of) datamodel(s)"""
        res = []
        if not many:
            recordset = recordset[:1]
        for record in recordset:
            instance = cls(partial=True)
            for model_field in cls._model_fields:
                schema_field = instance.__schema__.fields[model_field]
                nested_datamodel_name = getattr(schema_field, "datamodel_name", None)
                if nested_datamodel_name and record[model_field]:
                    nested_datamodel_class = recordset.env.datamodels[
                        nested_datamodel_name
                    ]
                    if hasattr(nested_datamodel_class, "from_recordset"):
                        setattr(
                            instance,
                            model_field,
                            nested_datamodel_class.from_recordset(
                                record[model_field], many=schema_field.many
                            ),
                        )
                else:
                    value = (
                        None if record[model_field] is False else record[model_field]
                    )
                    setattr(instance, model_field, value)
            res.append(instance)
        if res and not many:
            return res[0]
        return res

    def get_odoo_record(self):
        """Get an existing record matching `self`. Meant to be overridden"""
        model = self.env[self._model]
        if "id" in self._model_fields and getattr(self, "id", None):
            return model.browse(self.id)
        return self._new_odoo_record()

    def _new_odoo_record(self):
        model = self.env[self._model]
        default_values = model.default_get(model._fields.keys())
        return self.env[self._model].new(default_values)

    def _process_model_value(self, value, model_field):
        if hasattr(self, "validate_{}".format(model_field)):
            return getattr(self, "validate_{}".format(model_field))(value)
        return value

    def to_recordset(self, create=True):
        """Create or modify a recordset (singleton) related to self"""
        res = self.get_odoo_record() or self._new_odoo_record()
        self_fields = (
            self.dump().keys()
        )  # in case of partial not all fields are considered
        model_fields = set(self_fields) & set(self._model_fields)
        for model_field in model_fields:
            schema_field = self.__schema__.fields[model_field]
            if schema_field.dump_only:
                continue
            value = getattr(self, model_field)
            nested_datamodel_name = getattr(schema_field, "datamodel_name", None)
            if nested_datamodel_name:
                comodel = self.env[res._fields[model_field].comodel_name]
                value = [value] if isinstance(value, Datamodel) else value
                value = comodel.union(
                    *[
                        nested_instance.to_recordset(create=False)
                        for nested_instance in value
                    ]
                )
            res[model_field] = self._process_model_value(value, model_field)
        if create and isinstance(res.id, models.NewId):
            values = {field_name: res[field_name] for field_name in res._cache}
            values = res._convert_to_write(values)
            res = res.create(values)
        return res
