# Copyright 2020 Akretion
# Copyright 2020 Odoo SA (some code have been inspired from res_users code)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib

from odoo import _, fields, models
from odoo.exceptions import ValidationError


class DirectoryAuth(models.Model):
    _name = 'directory.auth'
    _description = 'Directory Auth'

    name = fields.Char(required=True)
    reset_password_token_duration = fields.Integer(
        default=1440,
        help="In minute, default 1440 minutes => 24h",
        )
    forget_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template",
        )
