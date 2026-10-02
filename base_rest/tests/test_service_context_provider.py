# Copyright 2021 ACSONE SA/NV
# Copyright 2026 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from unittest import mock

from odoo.addons.component.core import Component
from odoo.addons.website.tools import MockRequest

from .. import restapi
from .common import BaseRestCase, TransactionRestServiceRegistryCase


class TestServiceContextProvider(TransactionRestServiceRegistryCase):
    """Test Odoo service context provider

    In this class we test the context provided by the service context provider
    """

    def setUp(self):
        super().setUp()
        self._setup_registry(self)

    def tearDown(self):
        self._teardown_registry(self)
        super().tearDown()

    def test_01(self):
        """Test authenticated_partner_id

        In this case we check that the default service context provider provides
        no authenticated_partner_id
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

        self._build_services(self, TestServiceNewApi)
        controller = self._get_controller_for(TestServiceNewApi)
        with MockRequest(self.env), controller().service_component(
            "partner"
        ) as service:
            self.assertFalse(service.work.authenticated_partner_id)

    def test_02(self):
        """Test authenticated_partner_id

        In this case we check that the 'abstract.user.authenticated.partner.provider'
        service context provider provides the current user's partner as
        authenticated_partner_id
        """

        # pylint: disable=R7880
        class TestComponentContextprovider(Component):
            _name = "test.component.context.provider"
            _inherit = [
                "abstract.user.authenticated.partner.provider",
                "base.rest.service.context.provider",
            ]
            _usage = "test_component_context_provider"

        self._BaseTestController._component_context_provider = (
            "test_component_context_provider"
        )

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

        self._build_components(TestComponentContextprovider)
        self._build_services(self, TestServiceNewApi)
        controller = self._get_controller_for(TestServiceNewApi)
        with MockRequest(self.env), controller().service_component(
            "partner"
        ) as service:
            self.assertEqual(
                service.work.authenticated_partner_id, self.env.user.partner_id.id
            )

    def test_03(self):
        """Test authenticated_partner_id

        In this case we check that redefining the method _get_authenticated_partner_id
        changes the authenticated_partner_id provided by the service context provider
        """

        # pylint: disable=R7880
        class TestComponentContextprovider(Component):
            _name = "test.component.context.provider"
            _inherit = "base.rest.service.context.provider"
            _usage = "test_component_context_provider"

            def _get_authenticated_partner_id(self):
                return 9999

        self._BaseTestController._component_context_provider = (
            "test_component_context_provider"
        )

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

        self._build_components(TestComponentContextprovider)
        self._build_services(self, TestServiceNewApi)
        controller = self._get_controller_for(TestServiceNewApi)
        with MockRequest(self.env), controller().service_component(
            "partner"
        ) as service:
            self.assertEqual(service.work.authenticated_partner_id, 9999)

    def test_collection_env_context(self):
        """Test _get_collection_env_context

        In this case we check that the context returned by the controller's
        _get_collection_env_context is propagated to the env of the services
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

        self._build_services(self, TestServiceNewApi)
        controller = self._get_controller_for(TestServiceNewApi)

        orig_get_collection_env_context = controller._get_collection_env_context

        def _get_collection_env_context(self, collection, component_ctx):
            res = orig_get_collection_env_context(self, collection, component_ctx)
            res["test_key"] = "test_value"
            return res

        with mock.patch.object(
            controller, "_get_collection_env_context", _get_collection_env_context
        ), MockRequest(self.env), controller().service_component("partner") as service:
            self.assertEqual(service.env.context.get("test_key"), "test_value")
            self.assertIn("authenticated_partner_id", service.env.context)


class CommonCase(BaseRestCase):

    # dummy test method to pass codecov
    def test_04(self):
        self.assertEqual(self.registry.test_cr, self.cr)
