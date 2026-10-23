# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests

from odoo.http import Request, Response
from odoo.tests import HOST

from odoo.addons.api_log.tests.common import Common


class TestAPILog(Common):
    def test_log_request(self):
        base_url = self.base_url()
        secret_api_key = "my-secret-api-key"
        secret_cookie = "my-secret-biscuit"
        public_header_value = "public_header_value"
        httprequest = requests.Request(
            headers={
                "Api-Key": secret_api_key,
                "Cookie": secret_cookie,
                "Public-Header": public_header_value,
            },
            url=base_url,
            method="GET",
        )
        httprequest.remote_addr = HOST
        request = Request(httprequest)
        log = self.log_model.log_request(request)

        self.assertEqual(log.request_url, base_url)
        self.assertEqual(log.request_method, "GET")
        headers_values = log.request_headers.values()
        self.assertNotIn(secret_api_key, headers_values)
        self.assertNotIn(secret_cookie, headers_values)
        self.assertIn(public_header_value, headers_values)

    def test_name_empty_log(self):
        log = self.log_model.create({})
        self.assertEqual("0001-01-01 - [] ", log.name)

    def test_log_response(self):
        response = Response()
        log = self.log_model.create({})
        log.log_response(response)

        self.assertEqual(log.response_status_code, 200)
        self.assertEqual(log.response_headers["API-Log-Entry-ID"], str(log.id))
        self.assertEqual(response.headers["API-Log-Entry-ID"], str(log.id))

    def test_log_exception(self):
        log = self.log_model.create({})

        with self._mock_request_exc_handling(self.env):
            log.log_exception(Exception())

        self.assertEqual(log.response_headers["API-Log-Entry-ID"], str(log.id))

    def test_log_exception_none_headers(self):
        """
        If the exception's headers are None,
        it can be logged.
        """
        # Arrange
        log = self.log_model.create({})
        exception = Exception()
        exception.headers = None

        # Act
        with self._mock_request_exc_handling(self.env):
            log.log_exception(exception)

        # Assert
        self.assertEqual(log.response_headers["API-Log-Entry-ID"], str(log.id))
        self.assertTrue(log.stack_trace)

    def test_log_exception_readonly_headers(self):
        """
        If the exception's headers are readonly,
        they can be logged.
        """
        # Arrange
        log = self.log_model.create({})
        exc_headers = {
            "answer": 42,
        }

        class ReadOnlyException(Exception):
            @property
            def headers(self):
                return exc_headers.copy()

        ro_exception = ReadOnlyException()
        # pre-condition
        with self.assertRaises(AttributeError) as ae:
            ro_exception.headers = dict()
        self.assertIn("can't set attribute", str(ae.exception))

        # Act
        with self._mock_request_exc_handling(self.env):
            log.log_exception(ro_exception)

        # Assert
        self.assertLess(exc_headers.items(), log.response_headers.items())
