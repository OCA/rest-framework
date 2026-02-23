# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from pydantic import BaseModel

from .. import restapi


class TestPydantic(TransactionCase):
    def setUp(self):
        super().setUp()

        class Model1(BaseModel):
            name: str
            description: str = None

        self.Model1: BaseModel = Model1

    def _from_params(self, pydantic_cls: type[BaseModel], params: dict, **kwargs):
        restapi_pydantic_cls = (
            restapi.PydanticModelList
            if isinstance(params, list)
            else restapi.PydanticModel
        )
        restapi_pydantic = restapi_pydantic_cls(pydantic_cls, **kwargs)
        mock_service = mock.Mock()
        mock_service.env = self.env
        return restapi_pydantic.from_params(mock_service, params)

    def test_from_params(self):
        params = {
            "name": "Instance Name",
            "description": "Instance Description",
        }
        instance = self._from_params(self.Model1, params)
        self.assertEqual(instance.name, params["name"])
        self.assertEqual(instance.description, params["description"])

    def test_from_params_missing_optional_field(self):
        params = {"name": "Instance Name"}
        instance = self._from_params(self.Model1, params)
        self.assertEqual(instance.name, params["name"])
        self.assertIsNone(instance.description)

    def test_from_params_missing_required_field(self):
        msg = r"Field required"
        with self.assertRaisesRegex(UserError, msg):
            self._from_params(self.Model1, {"description": "Instance Description"})

    def test_from_params_pydantic_model_list(self):
        params = [
            {
                "name": "Instance Name",
                "description": "Instance Description",
            },
            {
                "name": "Instance Name 2",
                "description": "Instance Description 2",
            },
        ]
        instances = self._from_params(self.Model1, params)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].name, params[0]["name"])
        self.assertEqual(instances[0].description, params[0]["description"])
