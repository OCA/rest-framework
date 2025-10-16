# Copyright 2025 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).


from requests import Response

from odoo.addons.fastapi.tests.common import FastAPITransactionCase

from fastapi import status

from ..routers.user import user_router


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
        cls.default_fastapi_router = user_router
        cls.default_fastapi_running_user = cls.env["res.users"].create(
            {
                "name": "My demo user endpoint user",
                "login": "My_user_user_app",
            }
        )
        cls.default_fastapi_authenticated_partner = cls.env["res.partner"].create(
            {"name": "FastAPI Demo"}
        )

    def test_create_user(self) -> None:
        with self._create_test_client() as test_client:
            response: Response = test_client.post(
                "/user/create",
                params=[
                    {"name": "Test_one", "login": "Test_one", "company": "YourCompany"},
                    {"name": "Test_two", "login": "Test_two", "company": "YourCompany"},
                ],
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertDictEqual(
            response.json(), {"Test_one": "New ok", "Test_two": "New ok"}
        )


#     def test_who_ami(self) -> None:
#         with self._create_test_client() as test_client:
#             response: Response = test_client.get("/demo/who_ami")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         partner = self.default_fastapi_authenticated_partner
#         self.assertDictEqual(
#             response.json(),
#             {
#                 "name": partner.name,
#                 "display_name": partner.display_name,
#             },
#         )
#
#     def test_endpoint_info(self) -> None:
#         demo_app = self.env.ref("fastapi.fastapi_endpoint_demo")
#         with self._create_test_client(
#             dependency_overrides={fastapi_endpoint: partial(lambda a: a, demo_app)}
#         ) as test_client:
#             response: Response = test_client.get("/demo/endpoint_app_info")
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
#         self.assertDictEqual(
#             response.json(),
#             DemoEndpointAppInfo.model_validate(demo_app).model_dump(by_alias=True),
#         )
#
#     def test_exception_raised(self) -> None:
#         with self.assertRaisesRegex(UserError, "User Error"):
#             with self._create_test_client() as test_client:
#                 test_client.get(
#                     "/demo/exception",
#                     params={
#                         "exception_type": DemoExceptionType.user_error.value,
#                         "error_message": "User Error",
#                     },
#                 )
#
#         with self.assertRaisesRegex(NotImplementedError, "Bare Exception"):
#             with self._create_test_client() as test_client:
#                 test_client.get(
#                     "/demo/exception",
#                     params={
#                         "exception_type": DemoExceptionType.bare_exception.value,
#                         "error_message": "Bare Exception",
#                     },
#                 )
#
#     @mute_logger("odoo.addons.fastapi.tests.common")
#     def test_exception_not_raised(self) -> None:
#         with self._create_test_client(raise_server_exceptions=False) as test_client:
#             response: Response = test_client.get(
#                 "/demo/exception",
#                 params={
#                     "exception_type": DemoExceptionType.user_error.value,
#                     "error_message": "User Error",
#                 },
#             )
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertDictEqual(response.json(), {"detail": "User Error"})
#
#         with self._create_test_client(raise_server_exceptions=False) as test_client:
#             response: Response = test_client.get(
#                 "/demo/exception",
#                 params={
#                     "exception_type": DemoExceptionType.bare_exception.value,
#                     "error_message": "Bare Exception",
#                 },
#             )
#         self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
#         self.assertDictEqual(response.json(), {"detail": "Internal Server Error"})
#
# class TestPortalDoc(Commoncase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.default_fastapi_router = user_error
#
#         cls.user_one = cls.env["res.users"].create(
#             {
#                 "name": "Test_one",
#                 "login": "Test_one",
#             }
#         )
#
#     def test_create_user(self):
#         route = "/"
#
