# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    fastapi_log_mail_template_id = fields.Many2one(
        comodel_name="mail.template",
        domain=[("model_id.model", "=", "api.log")],
        string="Error E-mail Template",
        help="Select the email template that will be sent when an error is logged.",
    )
