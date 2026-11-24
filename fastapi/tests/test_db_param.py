# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from unittest.mock import MagicMock, patch

from odoo.tests.common import TransactionCase

from ..patch import _patched_set_session_and_dbname


class TestPatchSetSessionAndDbname(TransactionCase):
    """Tests for the _patched_set_session_and_dbname patch.

    The patch extends odoo.http.router._set_session_and_dbname to resolve the database
    from a ?db= query parameter or a Referer header when Odoo's normal session
    mechanism cannot determine the database (e.g. multi-database staging setups).
    """

    def _make_request(self, db_param="", referer=""):
        mock_request = MagicMock()
        mock_request.httprequest.args = {"db": db_param} if db_param else {}
        mock_request.httprequest.headers = {"Referer": referer} if referer else {}
        return mock_request

    def _call_patched(self, mock_request, original_return, db_filter_return):
        session, dbname = original_return
        mock_request.session = session
        mock_request.db = dbname
        mock_request.httprequest.environ = {"HTTP_HOST": "localhost"}

        def dummy_original(req):
            req.session = session
            req.db = dbname

        with (
            patch(
                "odoo.addons.fastapi.patch._original_set_session_and_dbname",
                side_effect=dummy_original,
            ),
            patch(
                "odoo.addons.fastapi.patch.db_filter",
                return_value=db_filter_return,
            ),
        ):
            _patched_set_session_and_dbname(mock_request)
            return mock_request.session, mock_request.db

    def test_db_already_resolved(self):
        """When the original method resolves a dbname, the patch must not interfere."""
        session = MagicMock()
        result_session, result_db = self._call_patched(
            self._make_request(),
            original_return=(session, "existing_db"),
            db_filter_return=["existing_db"],
        )
        self.assertEqual(result_db, "existing_db")
        self.assertEqual(result_session, session)

    def test_db_from_query_param(self):
        """When dbname is absent, resolve it from the ?db= query parameter."""
        session = MagicMock()
        _result_session, result_db = self._call_patched(
            self._make_request(db_param="mydb"),
            original_return=(session, None),
            db_filter_return=["mydb"],
        )
        self.assertEqual(result_db, "mydb")
        self.assertEqual(session.db, "mydb")

    def test_db_from_referer_header(self):
        """When ?db= is absent, fall back to the db param in the Referer header.

        This covers browser sub-requests (e.g. openapi.json, Swagger UI assets)
        where the Referer points to the docs page carrying ?db=.
        """
        session = MagicMock()
        _result_session, result_db = self._call_patched(
            self._make_request(referer="https://example.com/docs?db=mydb"),
            original_return=(session, None),
            db_filter_return=["mydb"],
        )
        self.assertEqual(result_db, "mydb")
        self.assertEqual(session.db, "mydb")

    def test_db_rejected_by_filter(self):
        """A db name that fails db_filter must not be used."""
        session = MagicMock()
        _result_session, result_db = self._call_patched(
            self._make_request(db_param="forbidden_db"),
            original_return=(session, None),
            db_filter_return=[],
        )
        self.assertIsNone(result_db)
        self.assertFalse(hasattr(session, "db") and session.db == "forbidden_db")
