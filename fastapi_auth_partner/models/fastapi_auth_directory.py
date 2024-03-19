# Copyright 2020 Akretion
# Copyright 2020 Odoo SA (some code have been inspired from res_users code)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class FastApiAuthDirectory(models.Model):
    _name = "fastapi.auth.directory"
    _description = "FastApi Auth Directory"

    name = fields.Char(required=True)
    set_password_token_duration = fields.Integer(
        default=1440, help="In minute, default 1440 minutes => 24h", required=True
    )
    request_reset_password_template_id = fields.Many2one(
        "mail.template", "Mail Template Forget Password", required=True
    )
    invite_set_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template New Password",
        required=True,
    )
    cookie_secret_key = fields.Char(
        required=True,
        groups="base.group_system",
    )
    cookie_duration = fields.Integer(
        default=525600,
        help="In minute, default 525600 minutes => 1 year",
        required=True,
    )
    count_partner = fields.Integer(compute="_compute_count_partner")

    def _compute_count_partner(self):
        data = self.env["fastapi.auth.partner"].read_group(
            [
                ("directory_id", "in", self.ids),
            ],
            ["directory_id"],
            groupby=["directory_id"],
            lazy=False,
        )
        res = {item["directory_id"][0]: item["__count"] for item in data}

        for record in self:
            record.count_partner = res.get(record.id, 0)

    @property
    def _server_env_fields(self):
        return {"cookie_secret_key": {}}
