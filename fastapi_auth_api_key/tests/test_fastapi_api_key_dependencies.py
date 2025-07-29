from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.fastapi_auth_api_key.dependencies import (
    authenticated_auth_api_key,
    authenticated_env_by_auth_api_key,
    authenticated_partner_by_api_key,
)

from fastapi.exceptions import HTTPException


@tagged("-at_install", "post_install")
class TestFastapiAuthApiKey(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        demo_user = cls.env.ref("base.user_demo")
        cls.demo_env = demo_user.with_user(demo_user).env
        cls.demo_endpoint = cls.env["fastapi.endpoint"].create(
            {
                "name": "Test Enpoint",
                "app": "demo",
                "root_path": "/path_demo",
                "demo_auth_method": "api_key",
                "user_id": demo_user.id,
            }
        )
        cls.setUpClassApiKey()

    @classmethod
    def setUpClassApiKey(cls):
        user_model = cls.env["res.users"].with_context(no_reset_password=True)
        cls.authorized_user = user_model.create(
            {
                "name": "John Authorized",
                "login": "johnauth",
            }
        )
        cls.unauthorized_user = user_model.create(
            {
                "name": "Bob Unauthorized",
                "login": "bobunauth",
            }
        )
        api_key_model = cls.env["auth.api.key"]
        cls.authorized_api_key = api_key_model.create(
            {
                "user_id": cls.authorized_user.id,
                "name": "Authorized api key",
                "key": "authorized_key",
            }
        )
        cls.unauthorized_api_key = api_key_model.create(
            {
                "user_id": cls.unauthorized_user.id,
                "name": "Unauthorized api key",
                "key": "unauthorized_key",
            }
        )
        api_key_group_model = cls.env["auth.api.key.group"]
        cls.authorized_api_key_group = api_key_group_model.create(
            {
                "name": "Authorized api key group",
                "code": "authorized_api_key_group",
                "auth_api_key_ids": [(6, 0, cls.authorized_api_key.ids)],
            }
        )
        cls.demo_endpoint.auth_api_key_group_id = cls.authorized_api_key_group

    def test_authenticated_auth_api_key_no_api_key(self):
        # An exception is raised when no api key is used
        with self.assertRaises(HTTPException) as error:
            authenticated_auth_api_key(False, self.demo_env, self.demo_endpoint)
        self.assertEqual(error.exception.detail, "Missing HTTP-API-KEY header")

    def test_authenticated_auth_api_key_no_api_key_found(self):
        # An exception is raised when no api key record is found
        with self.assertRaises(HTTPException) as error:
            authenticated_auth_api_key("404", self.demo_env, self.demo_endpoint)
        self.assertEqual(error.exception.detail, ("The key 404 is not allowed",))

    def test_authenticated_auth_api_key_unauthorized_key(self):
        # An exception is raised when unauthorized api key record is found
        with self.assertRaisesRegex(HTTPException, r"Unauthorized"):
            authenticated_auth_api_key(
                "unauthorized_key", self.demo_env, self.demo_endpoint
            )

    def test_authenticated_auth_api_key(self):
        result_key = authenticated_auth_api_key(
            "authorized_key", self.demo_env, self.demo_endpoint
        )
        self.assertEqual(result_key, self.authorized_api_key)

    def test_authenticated_auth_api_key_without_group(self):
        # test with no group set unauthorized is allow to access
        self.demo_endpoint.auth_api_key_group_id = False
        result_key = authenticated_auth_api_key(
            "unauthorized_key", self.demo_env, self.demo_endpoint
        )
        self.assertEqual(result_key, self.unauthorized_api_key)

    def test_authenticated_partner_by_api_key(self):
        result_partner = authenticated_partner_by_api_key(self.authorized_api_key)
        self.assertEqual(result_partner, self.authorized_user.partner_id)

    def test_authenticated_env_by_auth_api_key(self):
        result_env = authenticated_env_by_auth_api_key(self.authorized_api_key)
        self.assertEqual(result_env.user, self.authorized_user)
