# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import threading
from contextlib import contextmanager

from odoo import api
from odoo.api import SUPERUSER_ID
from odoo.modules.registry import Registry
from odoo.tests.common import RecordCapturer, get_db_name
from odoo.tests.test_cursor import TestCursor

from odoo.addons.api_log.tests.common import Common as CommonAPILog


class Common(CommonAPILog):
    @classmethod
    def setUpClass(cls):
        # Request logs are persisted through a dedicated database connection so
        # they survive endpoint exceptions (see ``setUp``). Odoo cursors use
        # REPEATABLE READ, so that connection (and the test cursor) only see rows
        # committed before their snapshot is taken. The fastapi demo endpoint
        # must therefore be committed *before* ``super().setUpClass()`` opens the
        # test cursor, otherwise neither the request nor the log cursor can see
        # it. Since 19.0 it is loaded on demand, so create it here on a
        # short-lived cursor that the ``with`` block commits on exit.
        with Registry(get_db_name())._db.cursor() as setup_cr:
            api.Environment(setup_cr, SUPERUSER_ID, {})[
                "fastapi.endpoint"
            ]._load_demo_data()
        # Registered *before* ``super().setUpClass()`` so it runs last in the LIFO
        # cleanup order, after the base class closed ``cls.cr``. ``cls.cr`` writes
        # (and row-locks) the endpoint below; deleting it from another connection
        # while that lock is held would deadlock.
        cls.addClassCleanup(cls._remove_demo_endpoint)
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

    @classmethod
    def _remove_demo_endpoint(cls):
        """Remove the fastapi demo endpoint committed in ``setUpClass``."""
        with Registry(get_db_name())._db.cursor() as cr:
            endpoint = api.Environment(cr, SUPERUSER_ID, {}).ref(
                "fastapi.fastapi_endpoint_demo", raise_if_not_found=False
            )
            if endpoint:
                endpoint.unlink()

    def setUp(self):
        super().setUp()
        # Use a side test cursor to be able to get exception logs
        reg = self.env.registry
        reg.test_log_lock = threading.RLock()
        reg.test_log_cr = TestCursor(reg._db.cursor(), reg.test_log_lock, False)

    def tearDown(self):
        reg = self.env.registry
        reg.test_log_cr.rollback()
        reg.test_log_cr.close()
        # Also close the real cursor to avoid unclosed errors
        reg.test_log_cr._cursor.close()
        reg.test_log_cr = None
        reg.test_log_lock = None
        super().tearDown()

    def _get_log_env(self):
        return self.env(cr=self.env.registry.test_log_cr)

    def _get_log_env_records(self, records):
        log_env = self._get_log_env()
        return log_env[records._name].browse(records.ids)

    @contextmanager
    def log_capturer(self):
        app = self.fastapi_demo_app
        log_env = self._get_log_env()
        with RecordCapturer(
            log_env[self.log_model._name],
            [("collection_ref", "=", f"{app._name},{app.id}")],
        ) as capturer:
            yield capturer
