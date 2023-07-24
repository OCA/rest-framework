# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from functools import partial
from unittest import mock

from requests import Response

from odoo.tools import mute_logger

from fastapi import status

from ..dependencies import fastapi_endpoint
from ..routers import demo_router
from ..schemas import DemoEndpointAppInfo, DemoExceptionType
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

    @mute_logger("odoo.addons.fastapi.error_handlers")
    def assert_exception_processed(
        self,
        exception_type: DemoExceptionType,
        error_message: str,
        expected_message: str,
        expected_status_code: int,
    ) -> None:
        demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
        with self._create_test_client(
            demo_app._get_app(), raise_server_exceptions=False
        ) as test_client, mock.patch.object(
            self.env.cr.__class__, "rollback"
        ) as mock_rollback:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": exception_type.value,
                    "error_message": error_message,
                },
            )
            mock_rollback.assert_called_once()
        self.assertEqual(response.status_code, expected_status_code)
        self.assertDictEqual(
            response.json(),
            {
                "detail": expected_message,
            },
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

    def test_user_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.user_error,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_validation_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.validation_error,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_bare_exception(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.bare_exception,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_access_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.access_error,
            error_message="test",
            expected_message="AccessError",
            expected_status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_missing_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.missing_error,
            error_message="test",
            expected_message="MissingError",
            expected_status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_http_exception(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.http_exception,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_409_CONFLICT,
        )
