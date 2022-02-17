# Copyright 2021 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


import os.path
from io import BytesIO

import requests

from odoo import _
from odoo.exceptions import MissingError
from odoo.http import content_disposition, request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AttachmentBase(Datamodel):
    _name = "ir.attachment.base"

    name = fields.String(required=False, allow_none=True)


class AttachmentInput(Datamodel):
    _name = "ir.attachment.input"
    _inherit = "ir.attachment.base"


class AttachmentOutput(Datamodel):
    _name = "ir.attachment.output"
    _inherit = "ir.attachment.base"

    id = fields.Integer(required=True, allow_none=False)


class AttachableOutput(Datamodel):
    _name = "attachable.output"

    attachments = fields.NestedModel("ir.attachment.output", required=False, many=True)


class AbstractAttachableService(AbstractComponent):
    """Abstract service to allow to use attachments on a service."""

    _name = "abstract.attachable.service"
    _inherit = "base.rest.service"
    _description = __doc__

    def _json_parser_attachments(self):
        res = [
            ("attachment_ids:attachments", ["id", "name"]),
        ]
        return res

    def _subvalidator_attachments(self):
        return {
            "type": "list",
            "schema": {
                "type": "dict",
                "schema": {"id": {"coerce": to_int}},
            },
        }

    @restapi.method(
        routes=[(["/<int:object_id>/attachments/<int:attachment_id>"], "GET")],
        output_param=restapi.BinaryData(required=True),
    )
    def download_attachment(self, object_id=None, attachment_id=None):
        record = self._get(object_id)
        self._check_attachment_access(record)
        attachment = self._get_attachment_for_record(record, attachment_id)
        content = None
        headers = [("X-Content-Type-Options", "nosniff")]
        if attachment.type == "url":
            r = requests.get(attachment.url)
            headers.extend(
                [
                    (
                        "Content-Type",
                        r.headers.get("Content-Type", attachment.mimetype),
                    ),
                    (
                        "Content-disposition",
                        r.headers.get(
                            "Content-Disposition", content_disposition(attachment.name)
                        ),
                    ),
                    ("Content-Length", r.headers.get("Content-Length", 0)),
                ]
            )
            content = BytesIO(r.content)
        else:
            headers.extend(
                [
                    ("Content-Type", attachment.mimetype),
                    ("Content-Disposition", content_disposition(attachment.name)),
                    ("Content-Length", len(attachment.raw)),
                ]
            )
            content = attachment.raw
        response = request.make_response(content, headers)
        response.status_code = 200
        return response

    @restapi.method(
        routes=[(["/<int:object_id>/attachments"], "POST")],
        input_param=restapi.MultipartFormData(
            {
                "file": restapi.BinaryData(required=True),
                "params": restapi.Datamodel("ir.attachment.input"),
            }
        ),
        output_param=restapi.Datamodel("ir.attachment.output"),
    )
    def create_attachment(self, object_id=None, file=None, params=None):
        record = self._get(object_id)
        self._check_attachment_access(record)
        vals = self._prepare_attachment_params(record, file, params.dump())
        attachment = self.env["ir.attachment"].create(vals)
        return self.env.datamodels["ir.attachment.output"].load(
            attachment.jsonify(["id", "name"])[0]
        )

    def _prepare_attachment_params(self, record, uploaded_file, params):
        params["res_id"] = record.id
        params["res_model"] = record._name
        params["raw"] = uploaded_file.read()
        if "name" not in params:
            params["name"] = os.path.basename(uploaded_file.filename)
        return params

    def _get(self, _id):
        record = self.env[self._expose_model].browse(_id)
        if not record:
            raise MissingError(_("The record does not exist: {}".format(_id)))
        else:
            return record

    def _get_attachment_for_record(self, record, _attachment_id):
        attachment = self.env["ir.attachment"].search(
            [
                ("id", "=", _attachment_id),
                ("res_id", "=", record.id),
                ("res_model", "=", record._name),
            ]
        )
        if not attachment:
            raise MissingError(_("The attachment %s does not exist") % (_attachment_id))
        else:
            return attachment

    def _check_attachment_access(self, record):
        # To help handling security when not using ir.rules
        pass
