# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import os

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.base_rest.tests.common import BaseRestCase
from odoo.addons.component.core import WorkContext
from odoo.addons.extendable.tests.common import ExtendableMixin

DATA_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)), "data")


class CommonCase(BaseRestCase, ExtendableMixin):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        collection = _PseudoCollection("base.rest.demo.private.services", cls.env)
        cls.private_services_env = WorkContext(
            model_name="rest.service.registration", collection=collection
        )

        collection = _PseudoCollection("base.rest.demo.public.services", cls.env)
        cls.public_services_env = WorkContext(
            model_name="rest.service.registration", collection=collection
        )
        collection = _PseudoCollection("base.rest.demo.new_api.services", cls.env)
        cls.new_api_services_env = WorkContext(
            model_name="rest.service.registration", collection=collection
        )
        cls.init_extendable_registry()

    @classmethod
    def tearDownClass(cls):
        cls.reset_extendable_registry()
        super().tearDownClass()

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not call
        # super)
        BaseRestCase.setUp(self)


def get_canonical_json(file_name):
    path = os.path.join(DATA_DIR, file_name)
    with open(path, "r") as f:
        return json.load(f)
