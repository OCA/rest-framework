# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json
import tempfile
from unittest import mock

from werkzeug.exceptions import BadRequest

from odoo.tests.common import BaseCase
from odoo.tools.config import config

from ..http import wrapJsonException


class TestWrapJsonException(BaseCase):
    def _get_body(self):
        exception = wrapJsonException(BadRequest("boom"), include_description=True)
        return json.loads(exception.get_body())

    def test_body(self):
        body = self._get_body()
        self.assertEqual(body["code"], 400)
        self.assertIn("boom", body["description"])
        self.assertNotIn("traceback", body)

    def test_body_dev_mode(self):
        with tempfile.NamedTemporaryFile("w", suffix=".conf") as rcfile:
            rcfile.write("[base_rest]\ndev_mode = True\n")
            rcfile.flush()
            with mock.patch.dict(config.options, {"config": rcfile.name}):
                body = self._get_body()
        self.assertIn("traceback", body)
