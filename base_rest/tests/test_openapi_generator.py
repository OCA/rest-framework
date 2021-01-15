# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import Component

from .. import restapi
from .common import TransactionRestServiceRegistryCase


class TestOpenAPIGenerator(TransactionRestServiceRegistryCase):
    """Test openapi document generation from REST services"""

    def setUp(self):
        super(TestOpenAPIGenerator, self).setUp()
        self.base_url = self.env["ir.config_parameter"].get_param("web.base.url")

    def test_01(self):
        """Simple test case"""

        # pylint: disable=R7980
        class PartnerService(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "Sercice description"

            @restapi.method(
                [(["/<int:id>/get", "/<int:id>"], "GET")],
                output_param=restapi.CerberusValidator("_get_partner_schema"),
                auth="public",
            )
            def get(self, _id):
                """Get the partner information"""

            def _get_partner_schema(self):
                return {"name": {"type": "string", "required": True}}

        self._build_services(PartnerService)
        service = self._get_service_component("partner")
        openapi = service.to_openapi()
        self.assertTrue(openapi)

        # The service url is available at base_url/controller._root_path/_usage
        url = openapi["servers"][0]["url"]
        self.assertEqual(self.base_url + "/test_controller/partner", url)

        # The title is generated from the service usage
        # The service info must contains a title and a description
        info = openapi["info"]
        self.assertEqual(info["title"], "%s REST services" % PartnerService._usage)
        self.assertEqual(info["description"], PartnerService._description)

        paths = openapi["paths"]
        # The paths must contains 2 entries (1 by routes)
        self.assertSetEqual({"/{id}/get", "/{id}"}, set(openapi["paths"]))

        for p in ["/{id}/get", "/{id}"]:
            path = paths[p]
            # The method for the paths is get
            self.assertIn("get", path)
            # The summary is the method docstring
            get = path["get"]
            self.assertEqual(get["summary"], "Get the partner information")
            # The reponse for status 200 is the openapi schema generated from
            # the cerberus schema returned by the _get_partner_schema method
            resp = None
            for item in get["responses"].items():
                if item[0] == "200":
                    resp = item[1]
            self.assertTrue(resp)
            self.assertDictEqual(
                resp,
                {
                    "content": {
                        "application/json": {
                            "schema": {
                                "properties": {"name": {"type": "string"}},
                                "required": ["name"],
                                "type": "object",
                            }
                        }
                    }
                },
            )

            # The path contains parameters
            self.assertDictEqual(
                path.get("parameters", [{}])[0],
                {
                    "in": "path",
                    "name": "id",
                    "required": True,
                    "schema": {"type": "integer", "format": "int32"},
                },
            )

    def test_02(self):
        """Test path parameters

        The new api allows you to define paths parameters. In this test
        we check that these parameters are into the openapi specification
        """

        # pylint: disable=R7980
        class PartnerService(Component):
            _inherit = "base.rest.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _description = "Sercice description"

            @restapi.method(
                [(["/<int:id>/update_name/<string:name>"], "POST")], auth="public"
            )
            def update_name(self, _id, _name):
                """update_name"""

        self._build_services(PartnerService)
        service = self._get_service_component("partner")
        openapi = service.to_openapi()
        self.assertTrue(openapi)
        paths = openapi["paths"]
        self.assertIn("/{id}/update_name/{name}", paths)
        path = paths["/{id}/update_name/{name}"]
        self.assertIn("post", path)
        parameters = path["parameters"]
        self.assertEqual(2, len(parameters))
        name_param = {}
        id_param = {}
        for p in parameters:
            if p["name"] == "id":
                id_param = p
            else:
                name_param = p
        self.assertDictEqual(
            name_param,
            {
                "in": "path",
                "name": "name",
                "required": True,
                "schema": {"type": "string"},
            },
        )
        self.assertDictEqual(
            id_param,
            {
                "in": "path",
                "name": "id",
                "required": True,
                "schema": {"type": "integer", "format": "int32"},
            },
        )
