# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from unittest import mock

from odoo.http import MISSING_CSRF_WARNING, Request
from odoo.tests.common import HttpCase, tagged
from odoo.tools import mute_logger

from .. import call
from . import controllers  # noqa: F401 # pylint: disable=unused-import

ROUTE = "/http_api_test"
CSRF_LOGGER = "odoo.addons.http_api_dispatcher.dispatcher"
ERRORS_LOGGER = "odoo.addons.http_api_dispatcher.errors"
MUTE = ("odoo.addons.http_api_dispatcher.errors", "odoo.http")


@tagged("-at_install", "post_install")
class TestDispatcher(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Test controllers are loaded after the routing map might have been built
        cls.env.registry.clear_cache("routing")

    def _post_json(self, path, data, **kw):
        headers = dict(kw.pop("headers", {}), **{"Content-Type": "application/json"})
        return self.url_open(ROUTE + path, data=json.dumps(data), headers=headers, **kw)

    def _get(self, path, **kw):
        return self.url_open(ROUTE + path, **kw)

    def test_input_validation(self):
        """Input is cleaned by the param; extra keys are dropped; JSON is returned."""
        response = self._post_json("/hello", {"name": " John ", "extra": "dropped"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/json")
        self.assertEqual(response.json(), {"greeting": "Hello John"})

    @mute_logger(*MUTE)
    def test_input_validation_error(self):
        """Invalid input gives a 400 w/ the errors in the JSON body."""
        response = self._post_json("/hello", {"nope": 1})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.json(),
            {
                "code": 400,
                "name": "Bad Request",
                "description": "BadRequest name",
                "errors": {"name": ["required"]},
            },
        )

    def test_input_non_dict(self):
        """A param can return a plain value, passed as the `input_kwarg`."""
        response = self._post_json("/hello_obj", {"name": "Jane"})
        self.assertEqual(response.json(), {"greeting": "Hello Jane"})

    def test_output_validation(self):
        """A valid result goes through the output param unchanged."""
        response = self._post_json("/hello_checked", {"name": "Jane"})
        self.assertEqual(response.json(), {"greeting": "Hello Jane"})

    @mute_logger(*MUTE)
    def test_output_validation_error(self):
        """An invalid result gives a generic 500, without details."""
        response = self._post_json("/hello_checked", {"name": "bad"})
        self.assertEqual(response.status_code, 500)
        self.assertEqual(
            response.json(), {"code": 500, "name": "Internal Server Error"}
        )

    def test_csrf_missing(self):
        """A CSRF protected route refuses requests w/o token (400) and logs why."""
        with (
            mock.patch.object(Request, "validate_csrf", return_value=False),
            self.assertLogs(CSRF_LOGGER, "WARNING") as warnings,
            self.assertLogs(ERRORS_LOGGER, "ERROR") as errors,
        ):
            response = self._post_json("/csrf", {"a": "1"})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            [rec.getMessage() for rec in warnings.records],
            [MISSING_CSRF_WARNING % "/http_api_test/csrf"],
        )
        # The url depends on the test server: only the rest is fixed
        self.assertRegex(
            errors.records[0].getMessage(),
            r"^RESTFULL call to url \S+/http_api_test/csrf with method POST "
            r"and params \{\} raise the following error "
            r"400 Bad Request: Session expired \(invalid CSRF token\)$",
        )
        self.assertEqual(len(errors.records), 1)

    def test_csrf_header(self):
        """The `X-CSRF-Token` header is the token checked on the request."""
        with mock.patch.object(
            Request, "validate_csrf", side_effect=lambda t: t == "good"
        ):
            response = self._post_json(
                "/csrf", {"a": "1"}, headers={"X-CSRF-Token": "good"}
            )
        self.assertEqual(response.json(), {"params": {"a": "1"}})

    def test_csrf_body(self):
        """Without header, the token is read from the body and kept out of params."""
        with mock.patch.object(
            Request, "validate_csrf", side_effect=lambda t: t == "good"
        ):
            response = self._post_json("/csrf", {"a": "1", "csrf_token": "good"})
        self.assertEqual(response.json(), {"params": {"a": "1"}})

    def test_query_only_param(self):
        """A param reading only the query never parses the body."""
        with mock.patch.object(call, "read_body", side_effect=AssertionError):
            response = self.url_open(
                ROUTE + "/query_only?page=2",
                data=json.dumps({"a": "1"}),
                headers={"Content-Type": "application/json"},
            )
        self.assertEqual(response.json(), {"page": "2"})

    @mute_logger(*MUTE)
    def test_invalid_json(self):
        """Malformed JSON gives a 400 'Invalid JSON data'."""
        response = self.url_open(
            ROUTE + "/hello",
            data="{nope",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid JSON data", response.json()["description"])

    def test_path_and_query(self):
        """Path and query params are merged; the path wins on conflicts."""
        response = self._get("/record/12?a=1&b=two&id=99")
        self.assertEqual(response.json(), {"id": 12, "params": {"a": "1", "b": "two"}})

    def test_form_body(self):
        """Form-encoded body params are parsed like JSON."""
        response = self.url_open(ROUTE + "/echo", data={"a": "1", "b": "2"})
        self.assertEqual(response.json(), {"params": {"a": "1", "b": "2"}})

    def test_json_body_and_query(self):
        """JSON body and query params are merged."""
        response = self._post_json("/echo?q=x", {"a": "1"})
        self.assertEqual(response.json(), {"params": {"a": "1", "q": "x"}})

    def test_method_not_allowed(self):
        """A route only accepts its declared methods (405 otherwise)."""
        response = self.url_open(ROUTE + "/record/1", data={"a": 1})
        self.assertEqual(response.status_code, 405)

    def test_prepare(self):
        """A hook can read request headers before the handler runs."""
        response = self._get("/prepare", headers={"Tag": "foo"})
        self.assertEqual(response.json(), {"tag": "foo"})

    def test_types(self):
        """Dates, datetimes and decimals are serialized as ISO strings and floats."""
        response = self._get("/types")
        self.assertEqual(
            response.json(),
            {"date": "2026-01-02", "datetime": "2026-01-02T03:04:05", "decimal": 1.5},
        )

    def test_raw_response(self):
        """A raw response is returned as is, w/ its own content type."""
        response = self._get("/raw")
        self.assertEqual(response.text, "raw")
        self.assertTrue(response.headers["Content-Type"].startswith("text/plain"))

    def test_lang(self):
        """The language follows `Accept-Language`, falling back to `en_US`."""
        self.env["res.lang"]._activate_lang("fr_FR")
        cases = (
            ("fr-BE,fr;q=0.9", "fr_FR"),
            ("fr-FR", "fr_FR"),
            ("de-DE,de;q=0.9", "en_US"),
            ("de-DE,fr;q=0.5", "fr_FR"),
        )
        for header, expected in cases:
            response = self._get("/lang", headers={"Accept-Language": header})
            self.assertEqual(response.json(), {"lang": expected}, header)

    @mute_logger(*MUTE)
    def test_errors(self):
        """Each error kind maps to its status code; no traceback in the body."""
        cases = (
            ("user", 400, {"description": "User error", "extra": "info"}),
            ("validation", 400, {"description": "Validation error"}),
            ("missing", 404, {}),
            ("access", 403, {}),
            ("boom", 500, {}),
            ("conflict", 500, {}),
        )
        for kind, code, extra in cases:
            response = self._get(f"/error/{kind}")
            self.assertEqual(response.status_code, code, kind)
            body = response.json()
            self.assertEqual(body["code"], code, kind)
            self.assertNotIn("traceback", body)
            for key, value in extra.items():
                self.assertEqual(body[key], value, kind)
            if not extra:
                self.assertNotIn("description", body, kind)

    @mute_logger(*MUTE)
    def test_error_map(self):
        """A custom error map turns an exception into the mapped status."""
        response = self._get("/conflict")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.json()["description"], "Already there")

    @mute_logger(*MUTE)
    def test_dev_mode(self):
        """In dev mode the error body includes the traceback."""

        def get_misc(section, key, default=None):
            return section == "base_rest" and key == "dev_mode"

        with mock.patch(
            "odoo.addons.http_api_dispatcher.errors.config.get_misc",
            side_effect=get_misc,
        ):
            response = self._get("/error/boom")
        body = response.json()
        self.assertIn("ValueError: Boom", body["traceback"])
        self.assertIn("description", body)
