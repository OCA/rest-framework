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
from odoo.addons.base_rest_pydantic.restapi import PydanticModel
from odoo.addons.component.core import AbstractComponent

from ..pydantic_models.attachment import AttachmentInfo, AttachmentRequest


class RestAttachmentServiceMixin(AbstractComponent):
    """Abstract service to allow to use attachments on a service."""

    _name = "rest.attachment.service.mixin"
    _inherit = "base.rest.service"
    _description = __doc__

    @restapi.method(
        routes=[(["/<int:object_id>/attachments/<int:attachment_id>"], "GET")],
        output_param=restapi.BinaryData(required=True),
    )
    def download_attachment(self, object_id=None, attachment_id=None):
        record = self._get(object_id)
        attachment = self._get_attachment_for_record(record, attachment_id)
        content, headers = self._get_attachment_response_data(attachment)
        response = request.make_response(content, headers)
        response.status_code = 200
        return response

    def _get_attachment_response_data(self, attachment):
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
        return content, headers

    @restapi.method(
        routes=[(["/<int:object_id>/attachments"], "POST")],
        input_param=restapi.MultipartFormData(
            {
                "file": restapi.BinaryData(required=True),
                "params": PydanticModel(AttachmentRequest),
            }
        ),
        output_param=PydanticModel(AttachmentInfo),
    )
    def create_attachment(self, object_id=None, file=None, params=None):
        record = self._get(object_id)
        vals = params.dict()
        vals["res_id"] = record.id
        vals["res_model"] = record._name
        vals["raw"] = file.read()
        if not vals.get("name"):
            vals["name"] = os.path.basename(file.filename)
        attachment = self.env["ir.attachment"].create(vals)
        return AttachmentInfo.from_orm(attachment)

    def _get(self, _id):
        record = self.env[self._expose_model].browse(_id)
        if not record:
            raise MissingError(_("The record does not exist: {}".format(_id)))
        else:
            self._check_attachment_access(record)
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
