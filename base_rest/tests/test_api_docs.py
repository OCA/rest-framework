from odoo.tests import HttpCase, tagged

from odoo.addons.component.core import Component

from .. import restapi
from .common import TransactionRestServiceRegistryCase


@tagged("post_install", "-at_install")
class TestAPIDocs(TransactionRestServiceRegistryCase, HttpCase):
    @classmethod
    def setUpClass(cls):
        """
        Avoids shadowing of "base_url" from RegistyCase class.
        """
        super().setUpClass()
        cls.base_url = lambda _self: cls.env["ir.config_parameter"].get_param(
            "web.base.url"
        )

    def setUp(self):
        super().setUp()

        self._setup_registry(self)

    def tearDown(self):
        self._teardown_registry(self)

        super().tearDown()

    def test_00_api_docs_no_data(self):
        """
        Makes sure the API Swagger page doesn't crash when we have no active endpoints.
        """
        self.authenticate("admin", "admin")
        response = self.url_open("/api-docs")

        self.assertEqual(response.status_code, 200)

        # Verify the content through a tour.
        self.start_tour(
            "/api-docs",
            "base_rest.tour_api_docs_no_content_validation",
            login="admin",
        )

    def test_01_api_docs_simple_request(self):
        """
        Adding a few controllers to the API, the Swagger interface should be fully
         functional. We won't test it itself, only that Odoo is sending the
         correct information.
        """

        class SimpleAPIEndpoint(Component):
            _inherit = "base.rest.service"
            _name = "simple.api.endpoint"
            _usage = "api"
            _collection = self._collection_name
            _description = "Simple API Endpoint"

            @restapi.method(
                [("/control-panel/pod_bay_doors/open", "POST")],
                auth="public",
                output_param=restapi.CerberusValidator(
                    {"result": {"type": "string", "required": True}}
                ),
            )
            def open_pod_bay_doors(self):
                return {"result": "I'm sorry, Dave. I'm afraid I can't do that."}

        self._build_services(self, SimpleAPIEndpoint)

        self.authenticate("admin", "admin")

        self.start_tour(
            "/api-docs",
            "base_rest.tour_api_docs_simple_api_endpoint",
            login="admin",
        )
