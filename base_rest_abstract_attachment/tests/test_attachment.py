# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import pathlib
import unittest

from werkzeug.datastructures import FileStorage

from odoo.addons.base_rest.tests.common import TransactionRestServiceRegistryCase
from odoo.addons.component.core import Component
from odoo.addons.datamodel.tests.common import TransactionDatamodelCase

from ..services.abstract_attachable import AbstractAttachableService


class AttachmentCommonCase(unittest.TestCase):
    def create_attachment(self, record_id, params=None):
        attrs = {"_object_id": record_id, "params": "{}"}
        res = None
        if params:
            attrs["params"] = json.dumps(params)
        with open(pathlib.Path(__file__).resolve()) as fp:
            attrs["file"] = FileStorage(fp)
            res = self.service.dispatch("create_attachment", params=attrs)
        return res


class AttachmentCase(
    AttachmentCommonCase, TransactionRestServiceRegistryCase, TransactionDatamodelCase
):
    def setUp(self):
        super().setUp()
        self._build_services(self, AbstractAttachableService)

        # pylint: disable=R7980
        class PartnerService(Component):
            _inherit = "abstract.attachable.service"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = self._collection_name
            _expose_model = "res.partner"

        self._build_services(self, PartnerService)
        self.service = self._get_service_component(self, "partner")

    def test_create_attachment(self):
        partner_id = self.ref("base.res_partner_1")
        res_upload = self.create_attachment(partner_id)
        self.assertEqual(res_upload["name"], "test_attachment.py")

    def test_create_attachment_custom_name(self):
        partner_id = self.ref("base.res_partner_1")
        res_upload = self.create_attachment(
            partner_id, params={"name": "CUSTOM_NAME.pdf"}
        )
        self.assertEqual(res_upload["name"], "CUSTOM_NAME.pdf")
