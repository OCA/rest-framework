# Copyright 2022 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import pathlib

from werkzeug.datastructures import FileStorage

from odoo.http import request

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext
from odoo.addons.component.tests.common import TransactionComponentCase
from odoo.addons.datamodel.tests.common import TransactionDatamodelCase


class AttachmentCommonCase(TransactionComponentCase, TransactionDatamodelCase):
    def setUp(self, collection_name="attachment.rest.services"):
        super().setUp()
        collection = _PseudoCollection(collection_name, self.env)
        self.services_env = WorkContext(
            model_name="rest.service.registration",
            collection=collection,
            request=request,
        )
        provider = self.services_env.component(usage="component_context_provider")
        provider._get_component_context()
        self.attachment_service = self.services_env.component(usage="attachment")

    def create_attachment(self, params=None):
        attrs = {"params": "{}"}
        if params:
            attrs["params"] = json.dumps(params)
        with open(pathlib.Path(__file__).resolve()) as fp:
            attrs["file"] = FileStorage(fp)
            self.attachment_res = self.attachment_service.dispatch(
                "create", params=attrs
            )
        return self.attachment_res


class AttachmentCase(AttachmentCommonCase):
    def test_create_attachment_one_step(self):
        res = self.create_attachment(
            params={
                "res_model": "res.partner",
                "res_id": self.ref("base.res_partner_1"),
            }
        )
        self.assertEqual(res["res_name"], "Wood Corner")
        self.assertEqual(res["res_model"], "res.partner")
        self.assertEqual(res["res_id"], self.ref("base.res_partner_1"))
        self.assertEqual(res["name"], "test_attachment.py")

    def test_create_attachment_two_step(self):
        res = self.create_attachment()
        self.assertEqual(res["res_name"], None)
        self.assertEqual(res["res_model"], None)
        self.assertEqual(res["res_id"], 0)
        self.assertEqual(res["name"], "test_attachment.py")
        res = self.attachment_service.dispatch(
            "update",
            res["id"],
            params={
                "res_id": self.ref("base.res_partner_1"),
                "res_model": "res.partner",
            },
        )
        self.assertEqual(res["res_model"], "res.partner")
        self.assertEqual(res["res_id"], self.ref("base.res_partner_1"))
        self.assertEqual(res["name"], "test_attachment.py")
