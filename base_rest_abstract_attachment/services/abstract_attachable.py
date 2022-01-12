# Copyright 2021 Akretion (https://www.akretion.com).
# @author Pierrick Brun <pierrick.brun@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import AbstractComponent
from odoo.addons.datamodel import fields
from odoo.addons.datamodel.core import Datamodel


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
