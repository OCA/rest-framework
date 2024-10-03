# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import os
import unittest
from contextlib import contextmanager

from odoo import sql_db
from odoo.tests.common import HttpCase
from odoo.tools import mute_logger

from fastapi import status

from ..schemas import DemoExceptionType


@unittest.skipIf(os.getenv("SKIP_HTTP_CASE"), "EndpointHttpCase skipped")
class FastAPIHttpCase(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fastapi_demo_app = cls.env.ref("fastapi.fastapi_endpoint_demo")
        cls.fastapi_demo_app._handle_registry_sync()
        lang = (
            cls.env["res.lang"]
            .with_context(active_test=False)
            .search([("code", "=", "fr_BE")])
        )
        lang.active = True

    @contextmanager
    def _mocked_commit(self):
        with unittest.mock.patch.object(
            sql_db.TestCursor, "commit", return_value=None
        ) as mocked_commit:
            yield mocked_commit

    def _assert_expected_lang(self, accept_language, expected_lang):
        route = "/fastapi_demo/demo/lang"
        response = self.url_open(route, headers={"Accept-language": accept_language})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, expected_lang)

    def test_call(self):
        route = "/fastapi_demo/demo/"
        response = self.url_open(route)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'{"Hello":"World"}')

    def test_lang(self):
        self._assert_expected_lang("fr,en;q=0.7,en-GB;q=0.3", b'"fr_BE"')
        self._assert_expected_lang("en,fr;q=0.7,en-GB;q=0.3", b'"en_US"')
        self._assert_expected_lang("fr-FR,en;q=0.7,en-GB;q=0.3", b'"fr_BE"')
        self._assert_expected_lang("fr-FR;q=0.1,en;q=1.0,en-GB;q=0.8", b'"en_US"')

    def test_retrying(self):
        """Test that the retrying mechanism is working as expected with the
        FastAPI endpoints.
        """
        nbr_retries = 3
        route = f"/fastapi_demo/demo/retrying?nbr_retries={nbr_retries}"
        response = self.url_open(route, timeout=20)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), nbr_retries)

    def test_retrying_post(self):
        """Test that the retrying mechanism is working as expected with the
        FastAPI endpoints in case of POST request with a file.
        """
        nbr_retries = 3
        route = f"/fastapi_demo/demo/retrying?nbr_retries={nbr_retries}"
        response = self.url_open(
            route, timeout=20, files={"file": ("test.txt", b"test")}
        )
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), {"retries": nbr_retries, "file": "test"})

    @mute_logger("odoo.http")
    def assert_exception_processed(
        self,
        exception_type: DemoExceptionType,
        error_message: str,
        expected_message: str,
        expected_status_code: int,
    ) -> None:
        with self._mocked_commit() as mocked_commit:
            route = (
                "/fastapi_demo/demo/exception?"
                f"exception_type={exception_type.value}&error_message={error_message}"
            )
            response = self.url_open(route, timeout=200)
            mocked_commit.assert_not_called()
            self.assertDictEqual(
                response.json(),
                {
                    "detail": expected_message,
                },
            )
            self.assertEqual(response.status_code, expected_status_code)

    def test_user_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.user_error,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_validation_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.validation_error,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_400_BAD_REQUEST,
        )

    def test_bare_exception(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.bare_exception,
            error_message="test",
            expected_message="Internal Server Error",
            expected_status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    def test_access_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.access_error,
            error_message="test",
            expected_message="AccessError",
            expected_status_code=status.HTTP_403_FORBIDDEN,
        )

    def test_missing_error(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.missing_error,
            error_message="test",
            expected_message="MissingError",
            expected_status_code=status.HTTP_404_NOT_FOUND,
        )

    def test_http_exception(self) -> None:
        self.assert_exception_processed(
            exception_type=DemoExceptionType.http_exception,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_409_CONFLICT,
        )

    @mute_logger("odoo.http")
    def test_request_validation_error(self) -> None:
        with self._mocked_commit() as mocked_commit:
            route = "/fastapi_demo/demo/exception?exception_type=BAD&error_message="
            response = self.url_open(route, timeout=200)
            mocked_commit.assert_not_called()
            self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def test_no_commit_on_exception(self) -> None:
        # this test check that the way we mock the cursor is working as expected
        # and that the transaction is rolled back in case of exception.
        with self._mocked_commit() as mocked_commit:
            url = "/fastapi_demo/demo"
            response = self.url_open(url, timeout=600)
            self.assertEqual(response.status_code, 200)
            mocked_commit.assert_called_once()

        self.assert_exception_processed(
            exception_type=DemoExceptionType.http_exception,
            error_message="test",
            expected_message="test",
            expected_status_code=status.HTTP_409_CONFLICT,
        )
