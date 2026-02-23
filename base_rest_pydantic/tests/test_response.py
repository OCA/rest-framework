# Copyright 2021 Wakari SRL
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from unittest import mock

from odoo.tests.common import TransactionCase

from pydantic import BaseModel

from .. import restapi


class TestPydantic(TransactionCase):
    def _to_response(self, instance: BaseModel):
        restapi_pydantic = restapi.PydanticModel(instance.__class__)
        mock_service = mock.Mock()
        mock_service.env = self.env
        return restapi_pydantic.to_response(mock_service, instance)

    def _to_response_list(self, instance: list[BaseModel]):
        restapi_pydantic = restapi.PydanticModelList(instance[0].__class__)
        mock_service = mock.Mock()
        mock_service.env = self.env
        return restapi_pydantic.to_response(mock_service, instance)

    def test_to_response(self):
        class Model1(BaseModel):
            name: str

        instance = Model1(name="Instance 1")
        res = self._to_response(instance)
        self.assertEqual(res["name"], instance.name)

    def test_to_response_validation_failed(self):
        class Model1(BaseModel):
            name: str = None

        instance = Model1(named="Instance 1")
        msg = r"Invalid Response"
        with self.assertRaisesRegex(SystemError, msg):
            self._to_response(instance)

    def test_to_response_list(self):
        class Model1(BaseModel):
            name: str

        instances = [Model1(name="Instance 1"), Model1(name="Instance 2")]
        res = self._to_response_list(instances)
        self.assertEqual(len(res), 2)
        self.assertSetEqual({r["name"] for r in res}, {"Instance 1", "Instance 2"})
