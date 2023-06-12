# Copyright 2020 Akretion
# Copyright 2020 Odoo SA (some code have been inspired from res_users code)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from datetime import datetime, timedelta

from itsdangerous import URLSafeTimedSerializer

from odoo import _, fields, models, tools
from odoo.exceptions import ValidationError
from odoo.http import request

COOKIE_AUTH_NAME = "partner_auth"


class DirectoryAuth(models.Model):
    _name = "directory.auth"
    _description = "Directory Auth"

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

    def _get_partner_from_request(self):
        self.ensure_one()
        # Keep in mind that in case of anonymous/guest partner
        # we do not have partner auth but we can have a valid cookie !
        # So we check if the cookie is valid and return a partner or a guest partner
        value = request.httprequest.cookies.get(COOKIE_AUTH_NAME)
        if value:
            vals = URLSafeTimedSerializer(self.cookie_secret_key).loads(
                value, max_age=self.cookie_duration * 60
            )
            if vals["did"] == self.id and vals["pid"]:
                partner = self.env["res.partner"].browse(vals["pid"]).exists()
                if partner.guest:
                    return partner
                else:
                    auth = partner.partner_auth_ids.filtered(
                        lambda s: s.directory_id == self
                    )
                    if auth:
                        return partner

    def _prepare_cookie_payload(self, partner_id):
        # use short key to reduce cookie size
        return {
            "did": self.id,
            "pid": partner_id,
        }

    def _prepare_cookie(self, partner_id):
        if not self.cookie_secret_key:
            raise ValidationError(_("No cookie secret key defined"))
        payload = self._prepare_cookie_payload(partner_id)
        value = URLSafeTimedSerializer(self.cookie_secret_key).dumps(payload)
        exp = (datetime.utcnow() + timedelta(minutes=self.cookie_duration)).timestamp()
        vals = {
            "value": value,
            "expires": exp,
            "httponly": True,
            "secure": True,
            "samesite": "strict",
        }
        if tools.config.get("test_enable"):
            # do not force https for test
            vals["secure"] = False
        return vals
