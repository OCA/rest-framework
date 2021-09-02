# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import mock

from odoo.exceptions import UserError

from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel
from odoo.addons.datamodel.tests import common

from .. import restapi


class TestDataModel(common.DatamodelRegistryCase):
    def setUp(self):
        super(TestDataModel, self).setUp()

        class Datamodel1(Datamodel):
            _name = "datamodel1"

            name = fields.String(required=True, allow_none=False)
            description = fields.String(required=False)

        Datamodel1._build_datamodel(self.datamodel_registry)

    def _from_params(self, datamodel_name, params, **kwargs):
        restapi_datamodel = restapi.Datamodel(datamodel_name, **kwargs)
        mock_service = mock.Mock()
        mock_service.env = self.env
        return restapi_datamodel.from_params(mock_service, params)

    def test_from_params(self):
        params = {"name": "Instance Name", "description": "Instance Description"}
        instance = self._from_params("datamodel1", params)
        self.assertEqual(instance.name, params["name"])
        self.assertEqual(instance.description, params["description"])

    def test_from_params_missing_optional_field(self):
        params = {"name": "Instance Name"}
        instance = self._from_params("datamodel1", params)
        self.assertEqual(instance.name, params["name"])
        self.assertIsNone(instance.description)

    def test_from_params_missing_required_field(self):
        msg = r"BadRequest {'name': \['Missing data for required field.'\]}"
        with self.assertRaisesRegex(UserError, msg):
            self._from_params("datamodel1", {"description": "Instance Description"})

    def test_from_partial_params_missing_required_field(self):
        params = {"description": "Instance Description"}
        instance = self._from_params("datamodel1", params, partial=True)
        self.assertEqual(instance.description, params["description"])
        self.assertIsNone(instance.name)
