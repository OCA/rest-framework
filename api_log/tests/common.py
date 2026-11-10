# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import HttpCase


class Common(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.log_model = cls.env["api.log"]
