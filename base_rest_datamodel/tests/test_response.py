# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import marshmallow
import mock

from odoo.addons.base_rest_datamodel import restapi
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.tests import common


class TestDataModel(common.DatamodelRegistryCase):
    def _to_response(self, instance):
        restapi_datamodel = restapi.Datamodel(instance._name)
        mock_service = mock.Mock()
        mock_service.env = self.env
        return restapi_datamodel.to_response(mock_service, instance)

    def test_to_response(self):
        class Datamodel1(Datamodel):
            _name = "datamodel1"

            name = fields.String(required=True, allow_none=False)

        Datamodel1._build_datamodel(self.datamodel_registry)
        instance = self.env.datamodels["datamodel1"](name="Instance 1")
        res = self._to_response(instance)
        self.assertEqual(res["name"], instance.name)

    def test_to_response_dump_only(self):
        class Datamodel2(Datamodel):
            _name = "datamodel2"

            name = fields.String(required=True, allow_none=False, dump_only=True)

        Datamodel2._build_datamodel(self.datamodel_registry)
        schema = self.env.datamodels["datamodel2"].get_schema()
        self.assertEqual(schema.unknown, "raise")
        msg = r"{'name': \['Unknown field.'\]}"
        with self.assertRaisesRegex(marshmallow.exceptions.ValidationError, msg):
            # confirmation that "name" cannot be loaded
            self.env.datamodels["datamodel2"].load({"name": "Failure"})
        instance = self.env.datamodels["datamodel2"](name="Instance 2")
        res = self._to_response(instance)
        self.assertEqual(res["name"], instance.name)
        # schema 'unknown' is back to "raise"
        self.assertEqual(schema.unknown, "raise")

    def test_to_response_dump_only_nested(self):
        class Datamodel3(Datamodel):
            _name = "datamodel3"

            child = fields.NestedModel("nested_datamodel")

        class NestedDatamodel(Datamodel):
            _name = "nested_datamodel"

            name = fields.String(required=True, allow_none=False, dump_only=True)

        NestedDatamodel._build_datamodel(self.datamodel_registry)
        Datamodel3._build_datamodel(self.datamodel_registry)
        for datamodel_name in ("datamodel3", "nested_datamodel"):
            schema = self.env.datamodels[datamodel_name].get_schema()
            self.assertEqual(schema.unknown, "raise")
        msg = r"{'name': \['Unknown field.'\]}"
        with self.assertRaisesRegex(marshmallow.exceptions.ValidationError, msg):
            # confirmation that child "name" cannot be loaded
            self.env.datamodels["datamodel3"].load({"child": {"name": "Failure"}})
        child_instance = NestedDatamodel(name="Child Instance")
        instance = self.env.datamodels["datamodel3"](child=child_instance)
        res = self._to_response(instance)
        self.assertEqual(res["child"]["name"], child_instance.name)
        for datamodel_name in ("datamodel3", "nested_datamodel"):
            schema = self.env.datamodels[datamodel_name].get_schema()
            # schema 'unknown' is back to "raise"
            self.assertEqual(schema.unknown, "raise")
