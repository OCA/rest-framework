# Copyright 2021 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import os.path

from odoo import _
from odoo.exceptions import MissingError, UserError
from odoo.http import content_disposition, request

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


class AttachmentBase(Datamodel):
    _name = "ir.attachment.base"

    name = fields.String(required=False, allow_none=True)
    res_id = fields.Integer(required=False, allow_none=True)
    res_model = fields.String(required=False, allow_none=True)


class AttachmentInput(Datamodel):
    _name = "ir.attachment.input"
    _inherit = "ir.attachment.base"


class AttachmentOutput(Datamodel):
    _name = "ir.attachment.output"
    _inherit = "ir.attachment.base"

    id = fields.Integer(required=True, allow_none=False)
    res_name = fields.String(required=False, allow_none=True)


class AttachmentService(Component):
    _name = "attachment.service"
    _inherit = "base.rest.service"
    _usage = "attachment"
    _expose_model = "ir.attachment"

    @restapi.method(
        routes=[(["/<int:_id>/download"], "GET")],
        output_param=restapi.BinaryData(required=True),
    )
    def download(self, _id):
        attachment = self._get(_id)
        if not attachment:
            raise MissingError()
        content = attachment.raw
        headers = [
            ("Content-Type", attachment.mimetype),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Disposition", content_disposition(attachment.name)),
            ("Content-Length", len(content)),
        ]
        response = request.make_response(content, headers)
        response.status_code = 200
        return response

    @restapi.method(
        routes=[(["/create"], "POST")],
        input_param=restapi.MultipartFormData(
            {
                "file": restapi.BinaryData(required=True),
                "params": restapi.Datamodel("ir.attachment.input"),
            }
        ),
        output_param=restapi.Datamodel("ir.attachment.output"),
    )
    # pylint: disable=W8106
    def create(self, file, params):
        vals = self._prepare_params(file, params.dump())
        attachment = self.env[self._expose_model].create(vals)
        return self.env.datamodels["{}.output".format(self._expose_model)].load(
            attachment.jsonify(["id", "name", "res_id", "res_model", "res_name"])[0]
        )

    @restapi.method(
        routes=[(["/<int:_id>/update"], "POST")],
        input_param=restapi.Datamodel("ir.attachment.input"),
        output_param=restapi.Datamodel("ir.attachment.output"),
    )
    def update(self, _id, params):
        attachment = self._get(_id)
        vals = self._prepare_params(None, params.dump())
        attachment.write(vals)
        return self.env.datamodels["{}.output".format(self._expose_model)].load(
            attachment.jsonify(["id", "name", "res_id", "res_model", "res_name"])[0]
        )

    def _prepare_params(self, uploaded_file, params):
        if params.get("res_id") and params.get("res_model"):
            record = self.env[params["res_model"]].browse(params["res_id"])
            if len(record) != 1:
                raise MissingError(
                    _(
                        "The targeted record does not exist: {}({})".format(
                            params["res_model"], params["res_id"]
                        )
                    )
                )
        elif not params.get("res_id") and not params.get("res_model"):
            params.pop("res_id", None)
            params.pop("res_model", None)
        else:
            raise UserError(_("You must provide both res_model and res_id"))
        if uploaded_file:
            params["raw"] = uploaded_file.read()
            if "name" not in params:
                params["name"] = os.path.basename(uploaded_file.filename)
        return params

    def _get(self, _id):
        record = self.env[self._expose_model].browse(_id)
        if not record:
            raise MissingError(
                _("The record %s %s does not exist") % (self._expose_model, _id)
            )
        else:
            return record
