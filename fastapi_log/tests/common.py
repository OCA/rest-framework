# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import threading
from contextlib import contextmanager

from odoo.sql_db import TestCursor
from odoo.tests.common import RecordCapturer

from odoo.addons.api_log.tests.common import Common as CommonAPILog


class Common(CommonAPILog):
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
            [("collection_ref", "=", "%s,%s" % (app._name, app.id))],
        ) as capturer:
            yield capturer
