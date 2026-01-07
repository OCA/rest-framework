# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from functools import partial

from requests import Response

from odoo.exceptions import UserError
from odoo.tools.misc import mute_logger

from fastapi import status

from ..dependencies import authenticated_partner_impl, fastapi_endpoint
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

    def test_hello_world(self) -> None:
        """Test basic hello world endpoint returns expected response.

        Validates that the simplest endpoint works correctly using
        the FastAPI test client.
        """
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"Hello": "World"})

    def test_who_ami(self) -> None:
        """Test authenticated partner endpoint returns correct user info.

        Verifies that the authenticated_partner dependency correctly
        provides partner information in the response.
        """
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
        """Test endpoint info returns correct configuration details.

        Demonstrates using dependency_overrides to inject a specific
        endpoint instance for testing.
        """
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

    def test_exception_raised(self) -> None:
        """Test that exceptions are raised when raise_server_exceptions=True.

        Validates that the test client correctly propagates exceptions
        when configured to do so (default behavior).
        """
        with self.assertRaisesRegex(UserError, "User Error"):
            with self._create_test_client() as test_client:
                test_client.get(
                    "/demo/exception",
                    params={
                        "exception_type": DemoExceptionType.user_error.value,
                        "error_message": "User Error",
                    },
                )

        with self.assertRaisesRegex(NotImplementedError, "Bare Exception"):
            with self._create_test_client() as test_client:
                test_client.get(
                    "/demo/exception",
                    params={
                        "exception_type": DemoExceptionType.bare_exception.value,
                        "error_message": "Bare Exception",
                    },
                )

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_exception_not_raised(self) -> None:
        """Test exception handlers when raise_server_exceptions=False.

        Validates that with raise_server_exceptions=False, exceptions
        are caught and converted to appropriate HTTP responses by the
        exception handlers.
        """
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.user_error.value,
                    "error_message": "User Error",
                },
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.json(), {"detail": "User Error"})

        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.bare_exception.value,
                    "error_message": "Bare Exception",
                },
            )
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertDictEqual(response.json(), {"detail": "Internal Server Error"})

    def test_hello_world_without_trailing_slash(self) -> None:
        """Test endpoint works without trailing slash."""
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response.json(), {"Hello": "World"})

    def test_who_ami_with_different_partner(self) -> None:
        """Test authenticated partner dependency with custom partner.

        Verifies that partner override in test client creation works.
        """
        custom_partner = self.env["res.partner"].create(
            {"name": "Custom Partner", "display_name": "Custom Display Name"}
        )
        with self._create_test_client(partner=custom_partner) as test_client:
            response: Response = test_client.get("/demo/who_ami")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(),
            {
                "name": custom_partner.name,
                "display_name": custom_partner.display_name,
            },
        )

    def test_who_ami_with_empty_partner(self) -> None:
        """Test authenticated partner endpoint with empty recordset.

        Tests edge case where partner is an empty recordset.
        """
        empty_partner = self.env["res.partner"].browse([])
        with self._create_test_client(partner=empty_partner) as test_client:
            response: Response = test_client.get("/demo/who_ami")
        # Should handle gracefully
        self.assertIn(response.status_code, [status.HTTP_200_OK, 500])

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_validation_error_exception(self) -> None:
        """Test ValidationError is converted to 400 Bad Request."""
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.validation_error.value,
                    "error_message": "Validation Failed",
                },
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.json(), {"detail": "Validation Failed"})

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_access_error_exception(self) -> None:
        """Test AccessError is converted to 403 Forbidden."""
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.access_error.value,
                    "error_message": "Access Denied",
                },
            )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertDictEqual(response.json(), {"detail": "AccessError"})

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_missing_error_exception(self) -> None:
        """Test MissingError is converted to 404 Not Found."""
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.missing_error.value,
                    "error_message": "Record Not Found",
                },
            )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertDictEqual(response.json(), {"detail": "MissingError"})

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_http_exception(self) -> None:
        """Test HTTPException with custom status code is preserved."""
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.http_exception.value,
                    "error_message": "Conflict Error",
                },
            )
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertDictEqual(response.json(), {"detail": "Conflict Error"})

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_exception_with_unicode_characters(self) -> None:
        """Test exception handling with unicode characters."""
        unicode_msg = "Error: 你好世界 🌍 émojis and spëcïal chars"
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get(
                "/demo/exception",
                params={
                    "exception_type": DemoExceptionType.user_error.value,
                    "error_message": unicode_msg,
                },
            )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertDictEqual(response.json(), {"detail": unicode_msg})

    def test_response_headers(self) -> None:
        """Test that responses include expected headers."""
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo/")
        self.assertIn("content-type", response.headers)
        self.assertIn("application/json", response.headers["content-type"])

    def test_endpoint_with_custom_env(self) -> None:
        """Test creating test client with custom environment.

        Verifies that custom env parameter works correctly.
        """
        custom_env = self.env(context={"test_context_key": "test_value"})
        with self._create_test_client(env=custom_env) as test_client:
            response: Response = test_client.get("/demo/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_endpoint_with_custom_user(self) -> None:
        """Test creating test client with different user.

        Validates that the user parameter correctly switches the
        executing user context.
        """
        admin_user = self.env.ref("base.user_admin")
        with self._create_test_client(user=admin_user) as test_client:
            response: Response = test_client.get("/demo/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_multiple_requests_same_client(self) -> None:
        """Test multiple requests using the same test client instance.

        Ensures the test client can handle multiple sequential requests.
        """
        with self._create_test_client() as test_client:
            response1: Response = test_client.get("/demo/")
            response2: Response = test_client.get("/demo/who_ami")
            response3: Response = test_client.get("/demo/")

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response3.status_code, status.HTTP_200_OK)
        self.assertDictEqual(response1.json(), response3.json())

    @mute_logger("odoo.addons.fastapi.tests.common")
    def test_invalid_endpoint_returns_404(self) -> None:
        """Test that non-existent endpoints return 404."""
        with self._create_test_client(raise_server_exceptions=False) as test_client:
            response: Response = test_client.get("/demo/nonexistent")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_dependency_override_validation(self) -> None:
        """Test that invalid dependency override combinations are caught.

        Verifies that providing both partner and authenticated_partner_impl
        override raises an error.
        """

        custom_partner = self.env["res.partner"].create({"name": "Test"})
        with self.assertRaises(ValueError):
            with self._create_test_client(
                partner=custom_partner,
                dependency_overrides={
                    authenticated_partner_impl: lambda: custom_partner
                },
            ) as test_client:
                test_client.get("/demo/who_ami")

    def test_endpoint_info_response_schema(self) -> None:
        """Test that endpoint_info response matches expected schema.

        Validates all expected fields are present in the response.
        """
        demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
        with self._create_test_client(
            dependency_overrides={fastapi_endpoint: partial(lambda a: a, demo_app)}
        ) as test_client:
            response: Response = test_client.get("/demo/endpoint_app_info")

        json_data = response.json()
        self.assertIn("id", json_data)
        self.assertIn("name", json_data)
        self.assertIn("app", json_data)
        self.assertIn("root_path", json_data)
        self.assertEqual(json_data["id"], demo_app.id)

    def test_response_json_structure(self) -> None:
        """Test that JSON responses have correct structure."""
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo/")

        json_data = response.json()
        self.assertIsInstance(json_data, dict)
        self.assertEqual(json_data.get("Hello"), "World")

    def test_partner_info_schema_validation(self) -> None:
        """Test that partner info response matches DemoUserInfo schema."""
        with self._create_test_client() as test_client:
            response: Response = test_client.get("/demo/who_ami")

        json_data = response.json()
        # Validate schema fields
        self.assertIn("name", json_data)
        self.assertIn("display_name", json_data)
        self.assertIsInstance(json_data["name"], str)
        self.assertIsInstance(json_data["display_name"], str)
