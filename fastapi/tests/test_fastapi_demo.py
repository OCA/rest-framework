# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from functools import partial

from requests import Response

from fastapi import status

from ..dependencies import fastapi_endpoint
from ..routers import demo_router
from ..schemas import DemoEndpointAppInfo
from .common import FastAPITransactionCase


class FastAPIDemoCase(FastAPITransactionCase):
    """The fastapi lib comes with a useful testclient that let's you
    easily test your endpoints. Moreover, the dependency overrides functionality
    allows you to provide specific implementation for part of the code to avoid
    to rely on some tricky http stuff for example: authentication

    This test class is an example on how you can test your own code
    """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.default_fastapi_router = demo_router
        cls.default_fastapi_running_user = cls.env.ref("fastapi.my_demo_app_user")
        cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
            {"name": "FastAPI Demo"}
        )

    def test_hello_world(self) -> None:
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"Hello": "World"})

    def test_who_ami(self) -> None:
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo/who_ami")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        partner = self.default_fastapi_authenticated_partner
        self.assertDictEqual(
            response.json(),
            {
                "name": partner.name,
                "display_name": partner.display_name,
            },
        )

    def test_endpoint_info(self) -> None:
        demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
        with self._create_test_client(
            dependency_overrides={fastapi_endpoint: partial(lambda a: a, demo_app)}
        ) as test_client:
            response: Response = test_client.get("/demo/endpoint_app_info")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            DemoEndpointAppInfo.model_validate(demo_app).model_dump(by_alias=True),
        )
