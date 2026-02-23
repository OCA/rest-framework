# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from contextlib import contextmanager

from odoo.addons.component.core import Component

from .. import restapi
from ..tools import ROUTING_DECORATOR_ATTR
from .common import TransactionRestServiceRegistryCase


class TestControllerBuilder(TransactionRestServiceRegistryCase):
    """Test Odoo controller builder

    In this class we test the generation of odoo controllers from the services
    component
    """

    def setUp(self):
        super().setUp()
        self._setup_registry(self)

    def tearDown(self):
        self._teardown_registry(self)
        super().tearDown()

    def test_01(self):
        """Test controller generated for old API services

        In this test we check that the controller generated for services with
        methods not decorated with the restapi.method decorator contains
        the required method to route requests to services. In the original
        implementation, these routes where hardcoded into the base controller.
        """

        # pylint: disable=R7980
        class TestServiceOldApi(Component):
            _inherit = "base.rest.service"
            _name = "test.ping.service"
            _usage = "ping"
            _collection = self._collection_name
            _description = "test"

            def get(self, _id, message):
                pass

            def search(self, message):
                return {"response": "Search called search with message " + message}

            def update(self, _id, message):
                return {"response": "PUT called with message " + message}

            # pylint:disable=method-required-super
            def create(self, **params):
                return {"response": "POST called with message " + params["message"]}

            def delete(self, _id):
                return {"response": f"DELETE called with id {_id} "}

            def my_method(self, **params):
                pass

            def my_instance_method(self, _id, **params):
                pass

            # Validator
            def _validator_search(self):
                return {"message": {"type": "string"}}

            # Validator
            def _validator_get(self):
                # no parameters by default
                return {}

            def _validator_update(self):
                return {"message": {"type": "string"}}

            def _validator_create(self):
                return {"message": {"type": "string"}}

            def _validator_my_method(self):
                return {"message": {"type": "string"}}

            def _validator_my_instance_method(self):
                return {"message": {"type": "string"}}

        self.assertFalse(self._get_controller_for(TestServiceOldApi))
        self._build_services(self, TestServiceOldApi)
        controller = self._get_controller_for(TestServiceOldApi)

        routes = self._get_controller_route_methods(controller)
        self.assertSetEqual(
            set(routes.keys()),
            {
                "get_get",
                "get_search",
                "post_update",
                "put_update",
                "post_create",
                "post_delete",
                "delete_delete",
                "post_my_method",
                "post_my_instance_method",
            }
            | self._controller_route_method_names,
        )
        self.assertTrue(controller)
        # the generated method_name is always the {http_method}_{method_name}
        method = routes["get_get"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/ping/<int:id>/get",
                    "/test_controller/ping/<int:id>",
                ],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["get_search"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/search", "/test_controller/ping/"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_update"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/ping/<int:id>/update",
                    "/test_controller/ping/<int:id>",
                ],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["put_update"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["PUT"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_create"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/create", "/test_controller/ping/"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_delete"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>/delete"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["delete_delete"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["DELETE"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_my_method"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/my_method"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_my_instance_method"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>/my_instance_method"],
                "save_session": True,
                "type": "restapi",
            },
        )

    def test_02(self):
        """Test controller generated from services with new API methods

        In this case we check that the generated controller for a service
        where the methods are decorated with restapi.method contains the
        required method to route the requests to the methods
        """

        # pylint: disable=R7980
        class TestServiceNewApi(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "test"

            @restapi.method(
                [(["/<int:id>/get", "/<int:id>"], "GET")],
                output_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="public",
            )
            def get(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            @restapi.method(
                [(["/<int:id>/get_name"], "GET")],
                output_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="public",
            )
            def get_name(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            @restapi.method(
                [(["/<int:id>/change_name"], "POST")],
                input_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="user",
            )
            def update_name(self, _id, **params):
                pass

            def _get_partner_schema(self):
                return {"name": {"type": "string", "required": True}}

        self.assertFalse(self._get_controller_for(TestServiceNewApi))
        self._build_services(self, TestServiceNewApi)
        controller = self._get_controller_for(TestServiceNewApi)

        routes = self._get_controller_route_methods(controller)
        self.assertSetEqual(
            set(routes.keys()),
            {"get_get", "get_get_name", "post_update_name"}
            | self._controller_route_method_names,
        )

        method = routes["get_get"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/partner/<int:id>/get",
                    "/test_controller/partner/<int:id>",
                ],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["get_get_name"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/get_name"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_update_name"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "user",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/change_name"],
                "save_session": True,
                "type": "restapi",
            },
        )

    def test_03(self):
        """Check that the controller builder takes care of services inheritance"""

        # pylint: disable=R7980
        class TestPartnerService(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "test"

            @restapi.method(
                [(["/<int:id>/get", "/<int:id>"], "GET")],
                output_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="public",
            )
            def get(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            def _get_partner_schema(self):
                return {"name": {"type": "string", "required": True}}

        class TestInheritPartnerService(Component):
            _inherit = "test.partner.service"

            @restapi.method(
                [(["/<int:id>/get_name"], "GET")],
                output_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="public",
            )
            def get_name(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            @restapi.method(
                [(["/<int:id>/change_name"], "POST")],
                input_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="user",
            )
            def update_name(self, _id, **params):
                pass

        self.assertFalse(self._get_controller_for(TestPartnerService))
        self._build_services(self, TestPartnerService, TestInheritPartnerService)
        controller = self._get_controller_for(TestPartnerService)

        routes = self._get_controller_route_methods(controller)
        self.assertSetEqual(
            set(routes.keys()),
            {"get_get", "get_get_name", "post_update_name"}
            | self._controller_route_method_names,
        )

        method = routes["get_get"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/partner/<int:id>/get",
                    "/test_controller/partner/<int:id>",
                ],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["get_get_name"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/get_name"],
                "save_session": True,
                "type": "restapi",
            },
        )

        method = routes["post_update_name"]
        self.assertDictEqual(
            getattr(method, ROUTING_DECORATOR_ATTR),
            {
                "methods": ["POST"],
                "auth": "user",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/change_name"],
                "save_session": True,
                "type": "restapi",
            },
        )


class TestControllerBuilder2(TransactionRestServiceRegistryCase):
    """Test Odoo controller builder

    In this class we test the generation of odoo controllers from the services
    component

    The test requires a fresh base controller
    """

    def setUp(self):
        super().setUp()
        self._setup_registry(self)

    def tearDown(self):
        self._teardown_registry(self)
        super().tearDown()

    def test_04(self):
        """Test controller generated from services with new API methods and
        old api takes into account the _default_auth
        Routes directly defined on the RestConroller without auth should also
        use the _default_auth
        """
        default_auth = "my_default_auth"
        default_cors = "*"
        default_csrf = True
        default_save_session = True
        self._BaseTestController._default_auth = default_auth
        self._BaseTestController._default_cors = default_cors
        self._BaseTestController._default_csrf = default_csrf
        self._BaseTestController._default_save_session = default_save_session

        # pylint: disable=R7980
        class TestService(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "test"

            @restapi.method(
                [(["/new_api_method_with"], "GET")],
                auth="public",
                cors="http://my_site",
                csrf=not default_csrf,
                save_session=not default_save_session,
            )
            def new_api_method_with(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            @restapi.method([(["/new_api_method_without"], "GET")])
            def new_api_method_without(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            # OLD API method
            def get(self, _id, message):
                pass

            # Validator
            def _validator_get(self):
                # no parameters by default
                return {}

        self._build_services(self, TestService)
        controller = self._get_controller_for(TestService)

        routes = self._get_controller_route_methods(controller)
        for attr, default in [
            ("auth", default_auth),
            ("cors", default_cors),
            ("csrf", default_csrf),
            ("save_session", default_save_session),
        ]:
            self.assertEqual(
                getattr(routes["get_new_api_method_without"], ROUTING_DECORATOR_ATTR)[
                    attr
                ],
                default,
                f"wrong {attr}",
            )
        self.assertEqual(
            getattr(routes["get_new_api_method_with"], ROUTING_DECORATOR_ATTR)["auth"],
            "public",
        )
        self.assertEqual(
            getattr(routes["get_new_api_method_with"], ROUTING_DECORATOR_ATTR)["cors"],
            "http://my_site",
        )
        self.assertEqual(
            getattr(routes["get_new_api_method_with"], ROUTING_DECORATOR_ATTR)["csrf"],
            not default_csrf,
        )
        self.assertEqual(
            getattr(routes["get_new_api_method_with"], ROUTING_DECORATOR_ATTR)[
                "save_session"
            ],
            not default_save_session,
        )

        self.assertEqual(
            getattr(routes["get_get"], ROUTING_DECORATOR_ATTR)["auth"],
            default_auth,
            "wrong auth for get_get",
        )

        for attr, default in [
            ("auth", default_auth),
            ("cors", default_cors),
            ("csrf", default_csrf),
            ("save_session", default_save_session),
        ]:
            self.assertEqual(
                getattr(routes["my_controller_route_without"], ROUTING_DECORATOR_ATTR)[
                    attr
                ],
                default,
                f"wrong {attr}",
            )

        routing = getattr(routes["my_controller_route_with"], ROUTING_DECORATOR_ATTR)
        for attr, value in [
            ("auth", "public"),
            ("cors", "http://with_cors"),
            ("csrf", "False"),
            ("save_session", "False"),
        ]:
            self.assertEqual(
                routing[attr],
                value,
                f"wrong {attr}",
            )
        self.assertEqual(
            getattr(
                routes["my_controller_route_without_auth_2"], ROUTING_DECORATOR_ATTR
            )["auth"],
            None,
            "wrong auth for my_controller_route_without_auth_2",
        )

    def test_05(self):
        """Test auth="public_or_default" on restapi.method

        The auth method on the route should be public_or_my_default_auth
        since the ir.http model provides the _auth_method_public_or_my_default_auth
        methods
        """
        default_auth = "my_default_auth"
        self._BaseTestController._default_auth = default_auth

        # pylint: disable=R7980
        class TestService(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "test"

            @restapi.method(
                [(["/new_api_method_with_public_or"], "GET")], auth="public_or_default"
            )
            def new_api_method_with_public_or(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            # Validator
            def _validator_get(self):
                # no parameters by default
                return {}

        # delare the auth méthod on ir.http
        with _add_method(
            self.env["ir.http"],
            "_auth_method_public_or_my_default_auth",
            lambda a: True,
        ):
            self._build_services(self, TestService)

        controller = self._get_controller_for(TestService)
        routes = self._get_controller_route_methods(controller)

        self.assertEqual(
            getattr(
                routes["get_new_api_method_with_public_or"], ROUTING_DECORATOR_ATTR
            )["auth"],
            "public_or_my_default_auth",
        )

    def test_06(self):
        """Test auth="public_or_default" on restapi.method

        The auth method on the route should be the default_auth configured on the
        controller since the ir.http model doesn't provide the
        _auth_method_public_or_my_default_auth methods
        """
        default_auth = "my_default_auth"
        self._BaseTestController._default_auth = default_auth

        # pylint: disable=R7980
        class TestService(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "test"

            @restapi.method(
                [(["/new_api_method_with_public_or"], "GET")], auth="public_or_default"
            )
            def new_api_method_with_public_or(self, _id):
                return {"name": self.env["res.partner"].browse(_id).name}

            # Validator
            def _validator_get(self):
                # no parameters by default
                return {}

        self._build_services(self, TestService)
        controller = self._get_controller_for(TestService)
        routes = self._get_controller_route_methods(controller)

        self.assertEqual(
            getattr(
                routes["get_new_api_method_with_public_or"], ROUTING_DECORATOR_ATTR
            )["auth"],
            "my_default_auth",
        )


@contextmanager
def _add_method(obj, name, method):
    try:
        setattr(obj.__class__, name, method)
        yield
    finally:
        delattr(obj.__class__, name)
