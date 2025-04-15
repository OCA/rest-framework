from odoo.tests.common import HttpCase


class CommonAPILog(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.log_model = cls.env["api.log"]
