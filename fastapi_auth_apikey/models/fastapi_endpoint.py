# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    apikey_auth_scope = fields.Char(
        default="fastapi",
        help="If using ApiKey auth in the APP endpoints, "
        "the keys with other scopes won't be accepted",
    )
