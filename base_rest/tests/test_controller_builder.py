# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.addons.component.core import Component

from .. import restapi
from .common import RestServiceRegistryCase


class TestControllerBuilder(RestServiceRegistryCase):
    """Test Odoo controller builder

    In this class we test the generation of odoo controllers from the services
    component
    """

    def setUp(self):
        super().setUp()
        RestServiceRegistryCase._setup_registry(self)

    def tearDown(self):
        super().tearDown()
        RestServiceRegistryCase._teardown_registry(self)

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
                return {"response": "DELETE called with id %s " % _id}

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
        self._build_services(TestServiceOldApi)
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
            },
        )
        self.assertTrue(controller)
        # the generated method_name is always the {http_method}_{method_name}
        method = routes["get_get"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/ping/<int:id>/get",
                    "/test_controller/ping/<int:id>",
                ],
            },
        )

        method = routes["get_search"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/search", "/test_controller/ping/"],
            },
        )

        method = routes["post_update"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/ping/<int:id>/update",
                    "/test_controller/ping/<int:id>",
                ],
            },
        )

        method = routes["put_update"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["PUT"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>"],
            },
        )

        method = routes["post_create"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/create", "/test_controller/ping/"],
            },
        )

        method = routes["post_delete"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>/delete"],
            },
        )

        method = routes["delete_delete"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["DELETE"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>"],
            },
        )

        method = routes["post_my_method"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/my_method"],
            },
        )

        method = routes["post_my_instance_method"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/ping/<int:id>/my_instance_method"],
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
        self._build_services(TestServiceNewApi)
        controller = self._get_controller_for(TestServiceNewApi)

        routes = self._get_controller_route_methods(controller)
        self.assertSetEqual(
            set(routes.keys()), {"get_get", "get_get_name", "post_update_name"}
        )

        method = routes["get_get"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/partner/<int:id>/get",
                    "/test_controller/partner/<int:id>",
                ],
            },
        )

        method = routes["get_get_name"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/get_name"],
            },
        )

        method = routes["post_update_name"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "user",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/change_name"],
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
        self._build_services(TestPartnerService, TestInheritPartnerService)
        controller = self._get_controller_for(TestPartnerService)

        routes = self._get_controller_route_methods(controller)
        self.assertSetEqual(
            set(routes.keys()), {"get_get", "get_get_name", "post_update_name"}
        )

        method = routes["get_get"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": [
                    "/test_controller/partner/<int:id>/get",
                    "/test_controller/partner/<int:id>",
                ],
            },
        )

        method = routes["get_get_name"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["GET"],
                "auth": "public",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/get_name"],
            },
        )

        method = routes["post_update_name"]
        self.assertDictEqual(
            method.routing,
            {
                "methods": ["POST"],
                "auth": "user",
                "cors": None,
                "csrf": False,
                "routes": ["/test_controller/partner/<int:id>/change_name"],
            },
        )
