# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import Component
from odoo.addons.website.tools import MockRequest

from .. import restapi
from .common import TransactionRestServiceRegistryCase


class TestOpenAPIGenerator(TransactionRestServiceRegistryCase):
    """Test openapi document generation from REST services"""

    def setUp(self):
        super().setUp()
        self._setup_registry(self)

    def tearDown(self):
        self._teardown_registry(self)
        super().tearDown()

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

        self._build_services(self, PartnerService)
        service = self._get_service_component(self, "partner")
        with MockRequest(self.env, url_root="https://example.com"):
            openapi = service.to_openapi()
        self.assertTrue(openapi)

        # The service url is available at base_url/controller._root_path/_usage
        servers = openapi.get("servers", [])
        self.assertEqual(len(servers), 2)
        expected = sorted(
            [
                f"{self.base_url}/test_controller/partner",
                "https://example.com/test_controller/partner",
            ]
        )
        self.assertListEqual(sorted([s["url"] for s in servers]), expected)

        # The title is generated from the service usage
        # The service info must contains a title and a description
        info = openapi["info"]
        self.assertEqual(info["title"], f"{PartnerService._usage} REST services")
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

        self._build_services(self, PartnerService)
        service = self._get_service_component(self, "partner")
        with MockRequest(self.env, url_root="https://example.com"):
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

    # pylint: disable=W8110
    def test_03(self):
        """Test default parameters and default responses

        You can define default parameters and responses at service level.
        In this test we check that these parameters and responses are into the
        openapi specification
        """
        default_params = [
            {
                "name": "API-KEY",
                "in": "header",
                "description": "API key for Authorization",
                "required": True,
                "schema": {"type": "string"},
                "style": "simple",
            }
        ]

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

            def _get_openapi_default_parameters(self):
                defaults = super()._get_openapi_default_parameters()
                defaults.extend(default_params)
                return defaults

            def _get_openapi_default_responses(self):
                responses = super()._get_openapi_default_responses().copy()
                responses["999"] = "TEST"
                return responses

        self._build_services(self, PartnerService)
        service = self._get_service_component(self, "partner")
        with MockRequest(self.env, url_root="https://example.com"):
            openapi = service.to_openapi()
        paths = openapi["paths"]
        self.assertIn("/{id}/update_name/{name}", paths)
        path = paths["/{id}/update_name/{name}"]
        self.assertIn("post", path)
        parameters = path["post"].get("parameters", [])
        self.assertListEqual(parameters, default_params)
        responses = path["post"].get("responses", [])
        self.assertIn("999", responses)

    def test_04(self):
        """Binary and Multipart form-data test case"""

        # pylint: disable=R7980
        class AttachmentService(Component):
            _inherit = "base.rest.service"
            _name = "test.attachment.service"
            _usage = "attachment"
            _collection = self._collection_name
            _description = "Sercice description"

            @restapi.method(
                routes=[(["/<int:id>/download"], "GET")],
                output_param=restapi.BinaryData(required=True),
            )
            def download(self, _id):
                """download the attachment"""

            @restapi.method(
                routes=[(["/create"], "POST")],
                input_param=restapi.MultipartFormData(
                    {
                        "file": restapi.BinaryData(
                            mediatypes=["image/png", "image/jpeg"]
                        ),
                        "params": restapi.CerberusValidator("_get_attachment_schema"),
                    }
                ),
                output_param=restapi.CerberusValidator("_get_attachment_schema"),
            )
            # pylint: disable=W8106
            def create(self, file, params):
                """create the attachment"""

            def _get_attachment_schema(self):
                return {"name": {"type": "string", "required": True}}

        self._build_services(self, AttachmentService)
        service = self._get_service_component(self, "attachment")
        with MockRequest(self.env, url_root="https://example.com"):
            openapi = service.to_openapi()
        paths = openapi["paths"]
        # The paths must contains 2 entries (1 by routes)
        self.assertSetEqual({"/{id}/download", "/create"}, set(openapi["paths"]))
        path_download = paths["/{id}/download"]
        resp_download = None
        for item in path_download["get"]["responses"].items():
            if item[0] == "200":
                resp_download = item[1]
        self.assertTrue(resp_download)
        self.assertDictEqual(
            resp_download,
            {
                "content": {
                    "*/*": {
                        "schema": {
                            "type": "string",
                            "format": "binary",
                            "required": True,
                        }
                    }
                }
            },
        )
        # The path contains parameters
        self.assertDictEqual(
            path_download.get("parameters", [{}])[0],
            {
                "in": "path",
                "name": "id",
                "required": True,
                "schema": {"type": "integer", "format": "int32"},
            },
        )
        path_create = paths["/create"]
        resp_create = None
        for item in path_create["post"]["responses"].items():
            if item[0] == "200":
                resp_create = item[1]
        self.assertTrue(resp_create)
        self.assertDictEqual(
            resp_create,
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
        request_create = path_create["post"]["requestBody"]
        self.assertDictEqual(
            request_create,
            {
                "content": {
                    "multipart/form-data": {
                        "schema": {
                            "type": "object",
                            "properties": {
                                "file": {
                                    "type": "string",
                                    "format": "binary",
                                    "required": False,
                                },
                                "params": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                        },
                                    },
                                    "required": ["name"],
                                },
                            },
                            "encoding": {
                                "file": {"contentType": "image/png, image/jpeg"}
                            },
                        }
                    }
                }
            },
        )
