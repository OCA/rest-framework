# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from functools import partial

from requests import Response

from odoo.tests.common import TransactionCase

from odoo.addons.fastapi import depends

from fastapi import status
from fastapi.testclient import TestClient


class FastAPIDemoCase(TransactionCase):
    """The fastapi lib comes with a usefull testclient that let's you
    easily test your endpoinds. Moreover, the dependey overrides functionnality
    allows you to provide specific implementation for part of the code to avoid
    to rely on some tricky http stuff for example: authentication

    This test class is an example on how you can test your own code
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.test_partner = cls.env["res.partner"].create({"name": "FastAPI Demo"})
        cls.fastapi_demo_app = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.app = cls.fastapi_demo_app._get_app()
        cls.app.dependency_overrides[depends.authenticated_partner_impl] = partial(
            lambda a: a, cls.test_partner
        )
        cls.app.dependency_overrides[depends.odoo_env] = partial(lambda a: a, cls.env)
        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.fastapi_demo_app._reset_app()

        super().tearDownClass()

    def _get_path(self, path) -> str:
        return self.fastapi_demo_app.root_path + path

    def test_hello_world(self) -> None:
        response: Response = self.client.get(self._get_path("/"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"Hello": "World"})

    def test_who_ami(self) -> None:
        response: Response = self.client.get(self._get_path("/who_ami"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(), {"name": "FastAPI Demo", "display_name": "FastAPI Demo"}
        )
