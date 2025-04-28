# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import requests

from odoo.http import Request, Response

from odoo.addons.api_log.tests.common import CommonAPILog


class TestAPILog(CommonAPILog):
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
        request = Request(httprequest)
        log = self.log_model.log_request(request)

        self.assertEqual(log.request_url, base_url)
        self.assertEqual(log.request_method, "GET")
        headers_values = log.request_headers.values()
        self.assertNotIn(secret_api_key, headers_values)
        self.assertNotIn(secret_cookie, headers_values)
        self.assertIn(public_header_value, headers_values)

    def test_log_response(self):
        response = Response()
        log = self.log_model.create({})
        log.log_response(response)

        self.assertEqual(log.response_status_code, 200)
