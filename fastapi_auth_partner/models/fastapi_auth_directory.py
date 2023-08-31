# Copyright 2020 Akretion
# Copyright 2020 Odoo SA (some code have been inspired from res_users code)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class FastApiAuthDirectory(models.Model):
    _name = "fastapi.auth.directory"
    _description = "FastApi Auth Directory"

    name = fields.Char(required=True)
    set_password_token_duration = fields.Integer(
        default=1440,
        help="In minute, default 1440 minutes => 24h",
    )
    forget_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template Forget Password",
    )
    invite_set_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template New Password",
    )
    cookie_secret_key = fields.Char()
    cookie_duration = fields.Integer(
        default=525600,
        help="In minute, default 525600 minutes => 1 year",
    )

    @property
    def _server_env_fields(self):
        return {"cookie_secret_key": {}}
