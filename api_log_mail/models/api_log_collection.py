# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class APILogCollection(models.AbstractModel):
    _inherit = "api.log_collection.mixin"

    api_log_mail_exception_template_id = fields.Many2one(
        comodel_name="mail.template",
        domain=[("model_id.model", "=", "api.log")],
        string="Error E-mail Template",
        help="An email based on this template will be sent when an error is logged.",
    )
    api_log_mail_exception_activity_type_id = fields.Many2one(
        comodel_name="mail.activity.type",
        domain=[("res_model", "=", "api.log")],
        string="Error Activity type",
        help="An activity of this type will be created when an error is logged.",
    )
