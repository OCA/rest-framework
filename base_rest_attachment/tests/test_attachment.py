# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import pathlib
import unittest

from werkzeug.datastructures import FileStorage

from odoo.addons.base_rest.tests.common import SavepointRestServiceRegistryCase
from odoo.addons.component.core import Component
from odoo.addons.extendable.tests.common import ExtendableMixin

from ..services.attachment_mixin import RestAttachmentServiceMixin


class AttachmentCommonCase(unittest.TestCase):
    def create_attachment(self, record_id, params=None):
        attrs = {"object_id": record_id, "params": "{}"}
        res = None
        if params:
            attrs["params"] = json.dumps(params)
        with open(pathlib.Path(__file__).resolve()) as fp:
            attrs["file"] = FileStorage(fp)
            res = self.service.dispatch("create_attachment", params=attrs)
        return res


class AttachmentCase(
    AttachmentCommonCase, SavepointRestServiceRegistryCase, ExtendableMixin
):

    # pylint: disable=W8106
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._build_services(cls, RestAttachmentServiceMixin)
        # pylint: disable=R7980

        class PartnerService(Component):
            _inherit = "rest.attachment.service.mixin"
            _name = "test.partner.service"
            _usage = "partner"
            _collection = cls._collection_name
            _expose_model = "res.partner"

        cls._build_services(cls, PartnerService)
        cls.service = cls._get_service_component(cls, "partner")

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
