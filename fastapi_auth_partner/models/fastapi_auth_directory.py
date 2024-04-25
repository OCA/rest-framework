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
    impersonating_token_duration = fields.Integer(
        default=1, help="In minute, default 1 minute", required=True
    )
    request_reset_password_template_id = fields.Many2one(
        "mail.template", "Mail Template Forget Password", required=True
    )
    invite_set_password_template_id = fields.Many2one(
        "mail.template",
        "Mail Template New Password",
        required=True,
    )
    invite_validate_email_template_id = fields.Many2one(
        "mail.template",
        "Mail Template Validate Email",
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

    fastapi_endpoint_ids = fields.One2many(
        "fastapi.endpoint",
        "directory_id",
        string="FastAPI Endpoints",
    )
    impersonating_user_ids = fields.Many2many(
        "res.users",
        "fastapi_auth_directory_impersonating_user_rel",
        "directory_id",
        "user_id",
        string="Impersonating Users",
        help="These odoo users can impersonate any partner of this directory",
        default=lambda self: (
            self.env.ref("base.user_root") | self.env.ref("base.user_admin")
        ).ids,
        groups="fastapi_auth_partner.group_partner_auth_manager",
    )

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
