# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from unittest import mock

from werkzeug.exceptions import Conflict, NotFound
from werkzeug.wrappers import Response

from odoo.exceptions import UserError
from odoo.tests.common import BaseCase

from ..errors import ApiValidationError, ErrorMapper, is_dev_mode


class TestErrors(BaseCase):
    def test_no_request(self):
        """Errors map to JSON responses without a request bound."""
        response = ErrorMapper().to_response(UserError("Nope"))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            json.loads(response.get_data()),
            {"code": 400, "name": "Bad Request", "description": "Nope"},
        )

    def test_validation_error(self):
        """A validation error gives a 400 w/ its errors."""
        exc = ApiValidationError("Invalid", errors={"a": ["required"]})
        body = json.loads(ErrorMapper().to_response(exc).get_data())
        self.assertEqual(body["errors"], {"a": ["required"]})
        self.assertEqual(body["code"], 400)

    def test_http_exception(self):
        """A werkzeug HTTP exception keeps its status code."""
        response = ErrorMapper().to_response(NotFound())
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json.loads(response.get_data())["code"], 404)

    def test_explicit_response(self):
        """An exception carrying its own response is returned as is."""
        exc = NotFound(response=Response("custom", status=418))
        self.assertIs(ErrorMapper().to_response(exc), exc)

    def test_routing_error_map(self):
        """A route's error map maps exceptions to their status."""
        mapper = ErrorMapper.for_routing({"error_map": [(KeyError, Conflict, False)]})
        response = mapper.to_response(KeyError("x"))
        self.assertEqual(response.status_code, 409)
        self.assertNotIn("description", json.loads(response.get_data()))

    def test_dev_mode_flag(self):
        """Dev mode is on only when its config flag is true."""
        cases = (
            ({}, False),
            ({"http_api": {"dev_mode": "False"}}, False),
            ({"http_api": {"dev_mode": "True"}}, True),
            ({"base_rest": {"dev_mode": "1"}}, True),
        )
        for misc, expected in cases:
            with mock.patch.dict(
                "odoo.addons.http_api_dispatcher.errors.config.misc", misc, clear=True
            ):
                self.assertEqual(is_dev_mode(), expected, misc)
