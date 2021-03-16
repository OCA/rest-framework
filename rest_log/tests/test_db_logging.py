# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# from urllib.parse import urlparse
import json

import mock

from odoo import exceptions
from odoo.tools import mute_logger

from .common import TestDBLoggingBase


class DBLoggingCase(TestDBLoggingBase):
    def test_log_enabled(self):
        self.service._log_calls_in_db = False
        with self._get_mocked_request():
            # no conf no flag
            self.assertFalse(self.service._db_logging_active())
            # by conf for collection
            self.env["ir.config_parameter"].sudo().set_param(
                "rest.log.active", self.service._collection
            )
            self.assertTrue(self.service._db_logging_active())
            # by conf for usage
            self.env["ir.config_parameter"].sudo().set_param(
                "rest.log.active", self.service._usage
            )
            self.assertTrue(self.service._db_logging_active())
            # no conf, service class flag
            self.env["ir.config_parameter"].sudo().set_param("rest.log.active", "")
            self.service._log_calls_in_db = True
            self.assertTrue(self.service._db_logging_active())

    def test_no_log_entry(self):
        self.service._log_calls_in_db = False
        log_entry_count = self.log_model.search_count([])
        with self._get_mocked_request():
            resp = self.service.dispatch("get", 100)
        self.assertNotIn("log_entry_url", resp)
        self.assertFalse(self.log_model.search_count([]) > log_entry_count)

    def test_log_entry(self):
        log_entry_count = self.log_model.search_count([])
        with self._get_mocked_request():
            resp = self.service.dispatch("get", 100)
        self.assertIn("log_entry_url", resp)
        self.assertTrue(self.log_model.search_count([]) > log_entry_count)

    # # TODO: this is very tricky because when the exception is raised
    # # the transaction is explicitly rolled back and then our test env is gone
    # # and everything right after is broken.
    # # To fully test this we need a different test class setup and advanced mocking
    # # and/or rewrite code so that we can it properly.
    # # def test_log_exception(self):
    # #     mock_path = \
    # #         "odoo.addons.REST.services.checkout.Checkout.scan_document"
    # #     log_entry_count = self.log_model.search_count([])
    # #     with self._get_mocked_request():
    # #         with mock.patch(mock_path, autospec=True) as mocked:
    # #             exc = exceptions.UserError("Sorry, you broke it!")
    # #             mocked.side_effect = exc
    # #             resp = self.service.dispatch(
    # #                 "scan_document", params={"barcode": self.picking.name})
    # #     self.assertIn("log_entry_url", resp)
    # #     self.assertTrue(self.log_model.search_count([]) > log_entry_count)
    # #     log_entry_data = urlparse(resp["log_entry_url"])
    # #     pass

    def test_log_entry_values_success(self):
        params = {"some": "value"}
        kw = {"result": {"data": "worked!"}}
        # test full data request only once, other tests will skip this part
        httprequest = mock.Mock(
            url="https://my.odoo.test/service/endpoint", method="POST"
        )
        extra_headers = {"KEEP-ME": "FOO"}
        with self._get_mocked_request(
            httprequest=httprequest, extra_headers=extra_headers
        ) as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, params=params, **kw
            )
        expected = {
            "request_url": httprequest.url,
            "request_method": httprequest.method,
            "state": "success",
            "error": False,
            "exception_name": False,
            "severity": False,
        }
        self.assertRecordValues(entry, [expected])
        expected_json = {
            "result": {"data": "worked!"},
            "params": dict(params),
            "headers": {
                "Cookie": "<redacted>",
                "Api-Key": "<redacted>",
                "KEEP-ME": "FOO",
            },
        }
        for k, v in expected_json.items():
            self.assertEqual(json.loads(entry[k]), v)

    def test_log_entry_values_failed(self):
        params = {"some": "value"}
        # no result, will fail
        kw = {"result": {}}
        with self._get_mocked_request() as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, params=params, **kw
            )
        expected = {
            "state": "failed",
            "result": "{}",
            "error": False,
            "exception_name": False,
            "severity": False,
        }
        self.assertRecordValues(entry, [expected])

    def _test_log_entry_values_failed_with_exception_default(self, severity=None):
        params = {"some": "value"}
        fake_tb = """
            [...]
            File "/somewhere/in/your/custom/code/file.py", line 503, in write
            [...]
            ValueError: Ops, something went wrong
        """
        orig_exception = ValueError("Ops, something went wrong")
        kw = {"result": {}, "traceback": fake_tb, "orig_exception": orig_exception}
        with self._get_mocked_request() as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, params=params, **kw
            )
        expected = {
            "state": "failed",
            "result": "{}",
            "error": fake_tb,
            "exception_name": "ValueError",
            "exception_message": "Ops, something went wrong",
            "severity": severity or "severe",
        }
        self.assertRecordValues(entry, [expected])

    def test_log_entry_values_failed_with_exception_default(self):
        self._test_log_entry_values_failed_with_exception_default()

    def test_log_entry_values_failed_with_exception_functional(self):
        params = {"some": "value"}
        fake_tb = """
            [...]
            File "/somewhere/in/your/custom/code/file.py", line 503, in write
            [...]
            UserError: You are doing something wrong Dave!
        """
        orig_exception = exceptions.UserError("You are doing something wrong Dave!")
        kw = {"result": {}, "traceback": fake_tb, "orig_exception": orig_exception}
        with self._get_mocked_request() as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, params=params, **kw
            )
        expected = {
            "state": "failed",
            "result": "{}",
            "error": fake_tb,
            "exception_name": "odoo.exceptions.UserError",
            "exception_message": "You are doing something wrong Dave!",
            "severity": "functional",
        }
        self.assertRecordValues(entry, [expected])

        # test that we can still change severity as we like
        entry.severity = "severe"
        self.assertEqual(entry.severity, "severe")

    def test_log_entry_severity_mapping_param(self):
        # test override of mapping via config param
        mapping = self.log_model._get_exception_severity_mapping()
        self.assertEqual(mapping, self.log_model.EXCEPTION_SEVERITY_MAPPING)
        self.assertEqual(mapping["ValueError"], "severe")
        self.assertEqual(mapping["odoo.exceptions.UserError"], "functional")
        value = "ValueError: warning, odoo.exceptions.UserError: severe"
        self.env["ir.config_parameter"].sudo().create(
            {"key": "rest.log.severity.exception.mapping", "value": value}
        )
        mapping = self.log_model._get_exception_severity_mapping()
        self.assertEqual(mapping["ValueError"], "warning")
        self.assertEqual(mapping["odoo.exceptions.UserError"], "severe")
        self._test_log_entry_values_failed_with_exception_default("warning")

    @mute_logger("odoo.addons.rest_log.models.rest_log")
    def test_log_entry_severity_mapping_param_bad_values(self):
        # bad values are discarded
        value = """
            ValueError: warning,
            odoo.exceptions.UserError::badvalue,
            VeryBadValue|error
        """
        self.env["ir.config_parameter"].sudo().create(
            {"key": "rest.log.severity.exception.mapping", "value": value}
        )
        mapping = self.log_model._get_exception_severity_mapping()
        expected = self.log_model.EXCEPTION_SEVERITY_MAPPING.copy()
        expected["ValueError"] = "warning"
        self.assertEqual(mapping, expected)
