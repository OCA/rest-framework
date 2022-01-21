# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# from urllib.parse import urlparse
import json

import mock

from odoo import exceptions
from odoo.tools import mute_logger

from odoo.addons.base_rest.tests.common import (
    SavepointRestServiceRegistryCase,
    TransactionRestServiceRegistryCase,
)
from odoo.addons.component.tests.common import new_rollbacked_env
from odoo.addons.rest_log import exceptions as log_exceptions  # pylint: disable=W7950

from .common import TestDBLoggingMixin


class TestDBLogging(SavepointRestServiceRegistryCase, TestDBLoggingMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls._get_service(cls)
        cls.log_model = cls.env["rest.log"].sudo()

    def test_log_enabled_conf_parsing(self):
        key1 = "coll1.service1.endpoint"
        key2 = "coll1.service2.endpoint:failed"
        key3 = "coll2.service1.endpoint:success"
        self.env["ir.config_parameter"].sudo().set_param(
            "rest.log.active", ",".join((key1, key2, key3))
        )
        expected = {
            # fmt:off
            "coll1.service1.endpoint": ("success", "failed"),
            "coll1.service2.endpoint": ("failed", ),
            "coll2.service1.endpoint": ("success", ),
            # fmt: on
        }
        self.assertEqual(self.env["rest.log"]._get_log_active_conf(), expected)

    def test_log_enabled(self):
        self.service._log_calls_in_db = False
        with self._get_mocked_request():
            # no conf no flag
            self.assertFalse(self.service._db_logging_active("avg_endpoint"))
            # by conf for collection
            self.env["ir.config_parameter"].sudo().set_param(
                "rest.log.active", self.service._collection
            )
            self.assertTrue(self.service._db_logging_active("avg_endpoint"))
            # by conf for usage
            self.env["ir.config_parameter"].sudo().set_param(
                "rest.log.active", self.service._collection + "." + self.service._usage
            )
            self.assertTrue(self.service._db_logging_active("avg_endpoint"))
            # by conf for usage and endpoint
            self.env["ir.config_parameter"].sudo().set_param(
                "rest.log.active",
                self.service._collection + "." + self.service._usage + ".avg_endpoint",
            )
            self.assertTrue(self.service._db_logging_active("avg_endpoint"))
            self.assertFalse(self.service._db_logging_active("not_so_avg_endpoint"))
            # no conf, service class flag
            self.env["ir.config_parameter"].sudo().set_param("rest.log.active", "")
            self.service._log_calls_in_db = True
            self.assertTrue(self.service._db_logging_active("avg_endpoint"))

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
                self.env, mocked_request, "avg_method", params=params, **kw
            )
        expected = {
            "collection": self.service._collection,
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
                self.env, mocked_request, "avg_method", params=params, **kw
            )
        expected = {
            "collection": self.service._collection,
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
                self.env, mocked_request, "avg_method", params=params, **kw
            )
        expected = {
            "collection": self.service._collection,
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
                self.env, mocked_request, "avg_method", params=params, **kw
            )
        expected = {
            "collection": self.service._collection,
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


class TestDBLoggingExceptionBase(
    TransactionRestServiceRegistryCase, TestDBLoggingMixin
):
    def setUp(self):
        super().setUp()
        self.service = self._get_service(self)

    def _test_exception(self, test_type, wrapping_exc, exc_name, severity):
        log_model = self.env["rest.log"].sudo()
        initial_entries = log_model.search([])
        entry_url_from_exc = None
        with self._get_mocked_request():
            try:
                self.service.dispatch("fail", test_type)
            except Exception as err:
                # Not using `assertRaises` to inspect the exception directly
                self.assertTrue(isinstance(err, wrapping_exc))
                self.assertEqual(
                    self.service._get_exception_message(err), "Failed as you wanted!"
                )
                entry_url_from_exc = err.rest_json_info["log_entry_url"]

        with new_rollbacked_env() as env:
            log_model = env["rest.log"].sudo()
            entry = log_model.search([]) - initial_entries
            expected = {
                "collection": self.service._collection,
                "state": "failed",
                "result": "null",
                "exception_name": exc_name,
                "exception_message": "Failed as you wanted!",
                "severity": severity,
            }
            self.assertRecordValues(entry, [expected])
            self.assertEqual(entry_url_from_exc, self.service._get_log_entry_url(entry))


class TestDBLoggingExceptionUserError(TestDBLoggingExceptionBase):
    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        # Override to avoid registering twice the same controller route.
        # Disclaimer: to run these tests w/ need TransactionCase
        # because the handling of the exception will do a savepoint rollback
        # which causes SavepointCase to fail.
        # When using the transaction case the rest_registry is initliazed
        # at every test, same for the test controller.
        # This leads to the error
        # "Only one REST controller
        # can be safely declared for root path /test_controller/"
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_user/"
        )

    def test_log_exception_user(self):
        self._test_exception(
            "user",
            log_exceptions.RESTServiceUserErrorException,
            "odoo.exceptions.UserError",
            "functional",
        )


class TestDBLoggingExceptionValidationError(TestDBLoggingExceptionBase):
    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_validation/"
        )

    def test_log_exception_validation(self):
        self._test_exception(
            "validation",
            log_exceptions.RESTServiceValidationErrorException,
            "odoo.exceptions.ValidationError",
            "functional",
        )


class TestDBLoggingExceptionValueError(TestDBLoggingExceptionBase):
    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_value/"
        )

    def test_log_exception_value(self):
        self._test_exception(
            "value", log_exceptions.RESTServiceDispatchException, "ValueError", "severe"
        )
