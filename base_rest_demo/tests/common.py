# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import os

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.base_rest.tests.common import BaseRestCase, RegistryMixin
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import SavepointComponentCase
from odoo.addons.datamodel.tests.common import SavepointDatamodelCase

DATA_DIR = os.path.join(os.path.realpath(os.path.dirname(__file__)), "data")


class CommonCase(BaseRestCase):
    @classmethod
    def setUpClass(cls):
        super(CommonCase, cls).setUpClass()
        collection = _PseudoCollection("base.rest.demo.private.services", cls.env)
        cls.private_services_env = WorkContext(
            model_name="rest.service.registration", collection=collection
        )

        collection = _PseudoCollection("base.rest.demo.public.services", cls.env)
        cls.public_services_env = WorkContext(
            model_name="rest.service.registration", collection=collection
        )


def get_canonical_json(file_name):
    path = os.path.join(DATA_DIR, file_name)
    with open(path, "r") as f:
        return json.load(f)


class NewServiceCommonCase(
    SavepointComponentCase, SavepointDatamodelCase, RegistryMixin
):
    @classmethod
    def _get_service(cls, service_name):
        collection = _PseudoCollection("base.rest.demo.new_api.services", cls.env)
        work = WorkContext(
            model_name="rest.service.registration", collection=collection
        )
        return work.component(usage=service_name)
