# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import os
import threading
import unittest
from contextlib import contextmanager

from odoo.sql_db import TestCursor
from odoo.tests.common import RecordCapturer

from odoo.addons.api_log.tests.common import CommonAPILog
from odoo.addons.fastapi.schemas import DemoExceptionType

from fastapi import status


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "FastAPIEncryptedErrorsCase skipped")
class FastAPIEncryptedErrorsCase(CommonAPILog):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fastapi_demo_app = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.fastapi_demo_app.root_path += "/test"
        cls.fastapi_demo_app._handle_registry_sync()
        cls.fastapi_demo_app.write({"log_requests": True})
        lang = (
            cls.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "=", "fr_BE")])
        )
        lang.active = True

    def setUp(self):
        super().setUp()
        # Use a side test cursor to be able to get exception logs
        reg = self.env.registry
        reg.test_log_lock = threading.RLock()
        reg.test_log_cr = TestCursor(reg._db.cursor(), reg.test_log_lock)

    def tearDown(self):
        reg = self.env.registry
        reg.test_log_cr.rollback()
        reg.test_log_cr.close()
        reg.test_log_cr = None
        reg.test_log_lock = None
        super().tearDown()

    @contextmanager
    def log_capturer(self):
        with RecordCapturer(
            self.env(cr=self.env.registry.test_log_cr)[self.log_model._name],
            [("fastapi_endpoint_id", "=", self.fastapi_demo_app.id)],
        ) as capturer:
            yield capturer

    def test_no_log_if_disabled(self):
        self.fastapi_demo_app.write({"log_requests": False})

        with self.log_capturer() as capturer:
            response = self.url_open("/fastapi_demo/test/demo", timeout=200)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(capturer.records)

    def test_log_simple(self):
        with self.log_capturer() as capturer:
            response = self.url_open("/fastapi_demo/test/demo", timeout=200)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(len(capturer.records), 1)
        log = capturer.records[0]
        self.assertTrue(log.request_url.endswith("/fastapi_demo/test/demo"))
        self.assertEqual(log.request_method, "GET")
        self.assertEqual(log.response_status_code, 200)
        self.assertTrue(log.time > 0)

    def test_log_exception(self):
        with self.log_capturer() as capturer:
            route = (
                "/fastapi_demo/test/demo/exception?"
                f"exception_type={DemoExceptionType.user_error.value}"
                "&error_message=User Error"
            )
            response = self.url_open(route, timeout=200)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(len(capturer.records), 1)
        log = capturer.records[0]
        self.assertIn("/fastapi_demo/test/demo/exception", log.request_url)
        self.assertEqual(log.request_method, "GET")
        self.assertEqual(log.response_status_code, 400)
        self.assertTrue(log.time > 0)
        self.assertTrue(log.response_body)
        self.assertIn(b"User Error", log.response_body)
        self.assertIn("odoo.exceptions.UserError: User Error\n", log.stack_trace)

    def test_log_bare_exception(self):
        with self.log_capturer() as capturer:
            route = (
                "/fastapi_demo/test/demo/exception?"
                f"exception_type={DemoExceptionType.bare_exception.value}"
                "&error_message=Internal Server Error"
            )
            response = self.url_open(route, timeout=200)
            self.assertEqual(
                response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        self.assertEqual(len(capturer.records), 1)
        log = capturer.records[0]
        self.assertIn("/fastapi_demo/test/demo/exception", log.request_url)
        self.assertEqual(log.request_method, "GET")
        self.assertEqual(log.response_status_code, 500)
        self.assertTrue(log.time > 0)
        self.assertTrue(log.response_body)
        self.assertIn(b"Internal Server Error", log.response_body)
        self.assertIn("NotImplementedError: Internal Server Error\n", log.stack_trace)

    def test_log_retrying_post(self):
        with self.log_capturer() as capturer:
            nbr_retries = 2
            route = f"/fastapi_demo/test/demo/retrying?nbr_retries={nbr_retries}"
            response = self.url_open(
                route, timeout=20, files={"file": ("test.txt", b"test")}
            )
            self.assertEqual(response.status_code, 200)
            self.assertDictEqual(
                response.json(), {"retries": nbr_retries, "file": "test"}
            )

        self.assertEqual(len(capturer.records), 3)
        for log in capturer.records[1:]:
            self.assertIn("/fastapi_demo/test/demo/retrying", log.request_url)
            self.assertEqual(log.request_method, "POST")
            self.assertEqual(log.response_status_code, 500)
            self.assertTrue(log.time > 0)
            self.assertTrue(log.response_body)
            self.assertIn(b"fake error", log.response_body)
            self.assertIn(
                "odoo.addons.fastapi.routers.demo_router.FakeConcurrentUpdateError: fake error",
                log.stack_trace,
            )

        log = capturer.records[0]
        self.assertIn("/fastapi_demo/test/demo/retrying", log.request_url)
        self.assertEqual(log.request_method, "POST")
        self.assertEqual(log.response_status_code, 200)
        self.assertTrue(log.time > 0)
        self.assertTrue(log.response_body)
        self.assertIn(b'"retries":2', log.response_body)
        self.assertIn(b'"file":"test"', log.response_body)
        self.assertFalse(log.stack_trace)

    def test_collection_ref(self):
        """The created log holds a reference to its endpoint and viceversa."""
        # Arrange
        endpoint = self.fastapi_demo_app
        # pre-condition
        self.assertFalse(endpoint.log_ids)

        # Act
        with self.log_capturer() as capturer:
            self.url_open("/fastapi_demo/test/demo", timeout=200)

        # Assert
        log = capturer.records[-1]
        self.assertEqual(log.collection_ref, endpoint)
        self.assertIn(log, endpoint.log_ids)
