# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from marshmallow import fields

from odoo import SUPERUSER_ID, fields as odoo_fields
from odoo.exceptions import ValidationError

from odoo.addons.datamodel.fields import NestedModel
from odoo.addons.datamodel.tests.common import DatamodelRegistryCase

from ..core import ModelSerializer
from ..field_converter import Binary
from ..serializers import GenericMinimalSerializer


def _schema_field(model_serializer_cls, field_name):
    schema_cls = model_serializer_cls.__schema_class__
    return schema_cls._declared_fields.get(field_name)


class TestModelSerializer(DatamodelRegistryCase):
    """Test build of ModelSerializer"""

    def setUp(self):
        super().setUp()
        self._full_build_model_serializer(GenericMinimalSerializer)

    def _full_build_model_serializer(self, model_serializer_cls):
        model_serializer_cls._build_datamodel(self.datamodel_registry)
        new_cls = model_serializer_cls._extend_from_odoo_model(
            self.datamodel_registry, self.env
        )
        new_cls._build_datamodel(self.datamodel_registry)
        return self.env.datamodels[model_serializer_cls._name]

    def _datamodel_instance(self, serializer_cls, values):
        datamodel_cls = self._full_build_model_serializer(serializer_cls)
        instance = datamodel_cls(partial=True)
        for key in values:
            setattr(instance, key, values[key])
        return instance

    def test_01_required_attrs(self):
        """Ensure that ModelSerializer has mandatory attributes"""
        msg = ".*require '_model' and '_model_fields' attributes.*"
        with self.assertRaisesRegex(ValidationError, msg):

            class ModelSerializerBad1(ModelSerializer):
                _name = "modelserializer_no_model"

            self._full_build_model_serializer(ModelSerializerBad1)

        with self.assertRaisesRegex(ValidationError, msg):

            class ModelSerializerBad2(ModelSerializer):
                _name = "modelserializer_no_model_fields"
                _model = "res.partner"

            self._full_build_model_serializer(ModelSerializerBad2)

    def test_02_has_field(self):
        """Ensure that ModelSerializers have the generated fields"""

        class ModelSerializer1(ModelSerializer):
            _name = "modelserializer1"
            _model = "res.partner"
            _model_fields = ["id"]

        class ModelSerializer2(ModelSerializer):
            _name = "modelserializer2"
            _inherit = "modelserializer1"

        for serializer_class in (ModelSerializer1, ModelSerializer2):
            full_cls = self._full_build_model_serializer(serializer_class)
            self.assertTrue(hasattr(full_cls, "id"))
            self.assertIsInstance(_schema_field(full_cls, "id"), fields.Integer)

    def test_03_simple_field_converter(self):
        """Ensure that non-relational fields are correctly converted"""

        fields_conversion = {
            "id": (odoo_fields.Id, fields.Integer, {"dump_only": True}),
            "create_date": (odoo_fields.Datetime, fields.DateTime, {"dump_only": True}),
            "date": (
                odoo_fields.Date,
                fields.Date,
                {"required": False, "allow_none": True},
            ),
            "name": (
                odoo_fields.Char,
                fields.String,
                {"required": False, "allow_none": True},
            ),
            "comment": (
                odoo_fields.Text,
                fields.String,
                {"required": False, "allow_none": True},
            ),
            "active": (
                odoo_fields.Boolean,
                fields.Boolean,
                {"required": False, "allow_none": True},
            ),
            "partner_latitude": (
                odoo_fields.Float,
                fields.Float,
                {"required": False, "allow_none": True},
            ),
            "active_lang_count": (
                odoo_fields.Integer,
                fields.Integer,
                {"dump_only": True},
            ),
            "image_1920": (
                odoo_fields.Image,
                Binary,
                {"required": False, "allow_none": True},
            ),
        }

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = list(fields_conversion)

        full_cls = self._full_build_model_serializer(PartnerSerializer)
        for field_name in fields_conversion:
            odoo_field_cls, marsh_field_cls, attrs = fields_conversion[field_name]
            this_field = _schema_field(full_cls, field_name)
            self.assertIsInstance(this_field, marsh_field_cls)
            for attr, attr_val in attrs.items():
                msg = (
                    "Error when converting field {}, wrong "
                    "attribute value ('{}' should be '{}')".format(
                        field_name, attr, attr_val
                    ),
                )
                self.assertEqual(getattr(this_field, attr), attr_val, msg=msg)

    def test_04_relational_field_converter(self):
        """Ensure that relational fields are correctly converted"""

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = ["user_id"]

        full_cls = self._full_build_model_serializer(PartnerSerializer)
        user_field = _schema_field(full_cls, "user_id")
        self.assertIsInstance(user_field, NestedModel)
        self.assertEqual(user_field.datamodel_name, "generic.minimal.serializer")
        self.assertFalse(user_field.many)

    def test_05_from_recordset(self):
        """Test `from_recordset` method with only simple fields"""

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = ["id", "name"]

        datamodel_cls = self._full_build_model_serializer(PartnerSerializer)
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        datamodel = datamodel_cls.from_recordset(self.partner)
        self.assertIsInstance(datamodel, datamodel_cls)
        self.assertEqual(datamodel.id, self.partner.id)
        self.assertEqual(datamodel.name, self.partner.name)
        self.assertEqual(
            set(PartnerSerializer._model_fields),
            set(datamodel.__schema__.fields.keys()),
        )

    def test_06_from_recordset_nested(self):
        """Test `from_recordset` method with nested fields, default nested serializer"""

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = ["user_id"]

        datamodel_cls = self._full_build_model_serializer(PartnerSerializer)
        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        datamodel1 = datamodel_cls.from_recordset(self.partner)
        self.assertIsInstance(datamodel1, datamodel_cls)
        self.assertEqual(datamodel1.user_id, None)
        self.partner.write({"user_id": SUPERUSER_ID})
        datamodel2 = datamodel_cls.from_recordset(self.partner)
        self.assertIsInstance(datamodel2, datamodel_cls)
        self.assertEqual(datamodel2.user_id.id, SUPERUSER_ID)
        self.assertEqual(
            datamodel2.user_id.display_name, self.partner.user_id.display_name
        )
        self.assertEqual(
            set(PartnerSerializer._model_fields),
            set(datamodel2.__schema__.fields.keys()),
        )

    def test_07_from_recordset_nested_custom(self):
        """Test `from_recordset` method with nested fields, custom nested serializer"""

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = ["user_id"]

            user_id = NestedModel("user_serializer")

        class UserSerializer(ModelSerializer):
            _name = "user_serializer"
            _model = "res.users"
            _model_fields = ["login"]

        user_dm_cls = self._full_build_model_serializer(UserSerializer)
        datamodel_cls = self._full_build_model_serializer(PartnerSerializer)
        user_field = _schema_field(datamodel_cls, "user_id")
        self.assertEqual(user_field.datamodel_name, "user_serializer")
        self.partner = self.env["res.partner"].create(
            {"name": "Test Partner", "user_id": SUPERUSER_ID}
        )
        datamodel = datamodel_cls.from_recordset(self.partner)
        self.assertIsInstance(datamodel.user_id, user_dm_cls)
        self.assertEqual(datamodel.user_id.login, self.partner.user_id.login)
        self.assertEqual(
            set(UserSerializer._model_fields),
            set(datamodel.user_id.__schema__.fields.keys()),
        )

    def test_08_to_recordset_write(self):
        """Test `to_recordset` method with only simple fields, existing partner"""

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = ["id", "name"]

        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        datamodel = self._datamodel_instance(
            PartnerSerializer,
            {"id": self.partner.id, "name": self.partner.name + "New"},
        )
        new_partner = datamodel.to_recordset()
        self.assertEqual(new_partner, self.partner)
        self.assertEqual(new_partner.name, datamodel.name)

    def test_09_to_recordset_relational_write(self):
        """Test `to_recordset` method with relational fields, existing partner"""

        class PartnerSerializer(ModelSerializer):
            _name = "partner_serializer"
            _model = "res.partner"
            _model_fields = ["id", "name", "child_ids"]

        self.partner = self.env["res.partner"].create({"name": "Test Partner"})
        self.child_partner = self.env["res.partner"].create(
            {"name": "Test Child Partner"}
        )
        datamodel_child = self._datamodel_instance(
            PartnerSerializer,
            {"id": self.child_partner.id, "name": self.child_partner.name + "New"},
        )
        datamodel_child2 = self._datamodel_instance(
            PartnerSerializer,
            {"name": "Newly Created Partner"},
        )
        datamodel = self._datamodel_instance(
            PartnerSerializer,
            {
                "id": self.partner.id,
                "name": self.partner.name + "New",
                "child_ids": [datamodel_child, datamodel_child2],
            },
        )
        new_partner = datamodel.to_recordset()
        new_partner_child = new_partner.child_ids.filtered(
            lambda p: p.id == self.child_partner.id
        )
        self.assertTrue(bool(new_partner_child))
        self.assertEqual(new_partner_child.name, datamodel_child.name)
        self.assertTrue("Newly Created Partner" in new_partner.child_ids.mapped("name"))
