# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    auth_api_key_group_id = fields.Many2one(
        "auth.api.key.group",
        help="If not set, all 'auth.api.key' are allowed to access to endpoints",
    )
