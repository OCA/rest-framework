# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import fields, models


class AuthDirectory(models.Model):
    _inherit = "auth.directory"

    fastapi_endpoint_ids = fields.One2many(
        "fastapi.endpoint",
        "directory_id",
        string="FastAPI Endpoints",
    )

    cookie_secret_key = fields.Char(
        groups="base.group_system",
        help="The secret key used to sign the cookie",
        required=True,
        default=lambda self: self._generate_default_secret_key(),
    )
    cookie_duration = fields.Integer(
        default=525600,
        help="In minute, default 525600 minutes => 1 year",
        required=True,
    )
    sliding_session = fields.Boolean()

    def action_regenerate_cookie_secret_key(self):
        self.ensure_one()
        self.cookie_secret_key = self._generate_default_secret_key()

    def _prepare_mail_context(self, context):
        rv = super()._prepare_mail_context(context)
        endpoint_id = self.env.context.get("_fastapi_endpoint_id")

        if endpoint_id:
            endpoint = self.env["fastapi.endpoint"].browse(endpoint_id)
            rv["public_url"] = endpoint.public_url or endpoint.public_api_url

        return rv

    @property
    def _server_env_fields(self):
        return {
            **super()._server_env_fields,
            "cookie_secret_key": {},
        }
