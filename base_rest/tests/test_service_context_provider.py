# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
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
        service_component = controller().service_component
        with (
            MockRequest(self.env),
            service_component(service_name="partner") as service,
        ):
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
        service_component = controller().service_component
        with (
            MockRequest(self.env),
            service_component(service_name="partner") as service,
        ):
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
        service_component = controller().service_component
        with (
            MockRequest(self.env),
            service_component(service_name="partner") as service,
        ):
            self.assertEqual(service.work.authenticated_partner_id, 9999)


class CommonCase(BaseRestCase):
    # dummy test method to pass codecov
    def test_04(self):
        self.assertEqual(self.registry.test_cr, self.cr)
