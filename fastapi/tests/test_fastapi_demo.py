# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from functools import partial
from unittest import mock

from requests import Response

from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger

from fastapi import status
from fastapi.testclient import TestClient

from .. import depends
from ..context import odoo_env_ctx
from ..models.fastapi_endpoint_demo import EndpointAppInfo, ExceptionType


class FastAPIDemoCase(TransactionCase):
    """The fastapi lib comes with a useful testclient that let's you
    easily test your endpoints. Moreover, the dependency overrides functionality
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
        # we need to disable the raise of unexpected exception into the called
        # service to test the error handling of the endpoint. By default, the
        # TestClient will let unexpected exception bubble up to the test method
        # to allows you to process the error accordingly
        cls.client = TestClient(cls.app, raise_server_exceptions=False)
        cls._ctx_token = odoo_env_ctx.set(
            cls.env(user=cls.env.ref("fastapi.my_demo_app_user"))
        )

    @classmethod
    def tearDownClass(cls) -> None:
        odoo_env_ctx.reset(cls._ctx_token)
        cls.fastapi_demo_app._reset_app()

        super().tearDownClass()

    def _get_path(self, path) -> str:
        return self.fastapi_demo_app.root_path + path

    @mute_logger("odoo.addons.fastapi.error_handlers")
    def assert_exception_processed(
        self,
        exception_type: ExceptionType,
        error_message: str,
        expected_message: str,
        expected_status_code: int,
    ) -> None:
        with mock.patch.object(self.env.cr.__class__, "rollback") as mock_rollback:
            response: Response = self.client.get(
                self._get_path("/exception"),
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
        response: Response = self.client.get(self._get_path("/"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"Hello": "World"})

    def test_who_ami(self) -> None:
        response: Response = self.client.get(self._get_path("/who_ami"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            {
                "name": self.test_partner.name,
                "display_name": self.test_partner.display_name,
            },
        )

    def test_endpoint_info(self) -> None:
        response: Response = self.client.get(self._get_path("/endpoint_app_info"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            EndpointAppInfo.from_orm(self.fastapi_demo_app).dict(by_alias=True),
        )

    def test_user_error(self) -> None:
        self.assert_exception_processed(
            exception_type=ExceptionType.user_error,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_validation_error(self) -> None:
        self.assert_exception_processed(
            exception_type=ExceptionType.validation_error,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_bare_exception(self) -> None:
        self.assert_exception_processed(
            exception_type=ExceptionType.bare_exception,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_access_error(self) -> None:
        self.assert_exception_processed(
            exception_type=ExceptionType.access_error,
            error_message="test",
            expected_message="AccessError",
            expected_status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_missing_error(self) -> None:
        self.assert_exception_processed(
            exception_type=ExceptionType.missing_error,
            error_message="test",
            expected_message="MissingError",
            expected_status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_http_exception(self) -> None:
        self.assert_exception_processed(
            exception_type=ExceptionType.http_exception,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_409_CONFLICT,
        )
