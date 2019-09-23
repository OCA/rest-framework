# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.http import controllers_per_module

from ..controllers.main import (
    BaseRestDemoNewApiController,
    BaseRestDemoPrivateApiController,
    BaseRestDemoPublicApiController,
)
from .common import CommonCase


class TestController(CommonCase):
    def test_controller_registry(self):
        # at the end of the start process, our tow controllers must into the
        # controller registered
        controllers = controllers_per_module["base_rest_demo"]
        self.assertEqual(len(controllers), 3)

        self.assertIn(
            (
                "odoo.addons.base_rest_demo.controllers.main."
                "BaseRestDemoPrivateApiController",
                BaseRestDemoPrivateApiController,
            ),
            controllers,
        )
        self.assertIn(
            (
                "odoo.addons.base_rest_demo.controllers.main."
                "BaseRestDemoPublicApiController",
                BaseRestDemoPublicApiController,
            ),
            controllers,
        )
        self.assertIn(
            (
                "odoo.addons.base_rest_demo.controllers.main."
                "BaseRestDemoNewApiController",
                BaseRestDemoNewApiController,
            ),
            controllers,
        )
