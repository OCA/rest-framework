# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

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

    @contextmanager
    def log_capturer(self):
        app = self.fastapi_demo_app
        with RecordCapturer(
            self.env[self.log_model._name],
            [("collection_ref", "=", "%s,%s" % (app._name, app.id))],
        ) as capturer:
            yield capturer
