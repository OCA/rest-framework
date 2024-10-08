# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging
from datetime import datetime, timedelta

import passlib
from itsdangerous import URLSafeTimedSerializer

from odoo import _, api, fields, models, tools
from odoo.exceptions import AccessDenied, UserError, ValidationError
from odoo.http import request

from odoo.addons.auth_signup.models.res_partner import random_token

# please read passlib great documentation
# https://passlib.readthedocs.io
# https://passlib.readthedocs.io/en/stable/narr/quickstart.html#choosing-a-hash
# be carefull odoo requirements use an old version of passlib
# TODO: replace with a JWT token
DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(["pbkdf2_sha512"])
DEFAULT_CRYPT_CONTEXT_TOKEN = passlib.context.CryptContext(
    ["pbkdf2_sha512"], pbkdf2_sha512__salt_size=0
)


_logger = logging.getLogger(__name__)


COOKIE_AUTH_NAME = "fastapi_auth_partner"


class FastApiAuthPartner(models.Model):
    _name = "fastapi.auth.partner"
    _description = "FastApi Auth Partner"
    _rec_name = "login"

    partner_id = fields.Many2one(
        "res.partner", "Partner", required=True, ondelete="cascade", index=True
    )
    directory_id = fields.Many2one(
        "fastapi.auth.directory", "Directory", required=True, index=True
    )
    user_can_impersonate = fields.Boolean(
        compute="_compute_user_can_impersonate",
        help="Technical field to check if the user can impersonate",
    )
    impersonating_user_ids = fields.Many2many(
        related="directory_id.impersonating_user_ids",
    )
    login = fields.Char(compute="_compute_login", store=True, required=True, index=True)
    password = fields.Char(compute="_compute_password", inverse="_inverse_password")
    encrypted_password = fields.Char(index=True)
    token_set_password_encrypted = fields.Char()
    token_expiration = fields.Datetime()
    token_impersonating_encrypted = fields.Char()
    token_impersonating_expiration = fields.Datetime()
    nbr_pending_reset_sent = fields.Integer(
        index=True,
        help=(
            "Number of pending reset sent from your customer."
            "This field is usefull when after a migration from an other system "
            "you ask all you customer to reset their password and you send"
            "different mail depending on the number of reminder"
        ),
    )
    date_last_request_reset_pwd = fields.Datetime(
        help="Date of the last password reset request"
    )
    date_last_sucessfull_reset_pwd = fields.Datetime(
        help="Date of the last sucessfull password reset"
    )

    token_mail_validation_encrypted = fields.Char()
    mail_verified = fields.Boolean(
        help="This field is set to True when the user has clicked on the link sent by email"
    )

    _sql_constraints = [
        (
            "directory_login_uniq",
            "unique (directory_id, login)",
            "Login must be uniq per directory !",
        ),
    ]

    # hack to solve sql constraint
    def _add_login_for_create(self, data):
        partner = self.env["res.partner"].browse(data["partner_id"])
        data["login"] = partner.email

    @api.model_create_multi
    def create(self, data_list):
        for data in data_list:
            self._add_login_for_create(data)
        return super().create(data_list)

    @api.depends("partner_id.email")
    def _compute_login(self):
        for record in self:
            record.login = record.partner_id.email

    def _crypt_context(self):
        return DEFAULT_CRYPT_CONTEXT

    def _check_no_empty(self, login, password):
        # double check by security but calling this through a service should
        # already have check this
        if not (
            isinstance(password, str) and password and isinstance(login, str) and login
        ):
            _logger.warning("Invalid login/password for sign in")
            raise AccessDenied()

    def _get_hashed_password(self, directory, login):
        self.flush()
        self.env.cr.execute(
            """
            SELECT id, COALESCE(encrypted_password, '')
            FROM fastapi_auth_partner
            WHERE login=%s AND directory_id=%s""",
            (login, directory.id),
        )
        hashed = self.env.cr.fetchone()
        if hashed and hashed[1]:
            # ensure that we have a partner_auth and this partner have a password set
            return hashed
        else:
            raise AccessDenied()

    def _compute_password(self):
        for record in self:
            record.password = ""

    def _inverse_password(self):
        # TODO add check on group
        for record in self:
            ctx = record._crypt_context()
            record.encrypted_password = ctx.encrypt(record.password)

    @api.model
    def log_in(self, directory, login, password):
        self._check_no_empty(login, password)
        _id, hashed = self._get_hashed_password(directory, login)
        valid, replacement = self._crypt_context().verify_and_update(password, hashed)

        if replacement is not None:
            self.browse(_id).encrypted_password = replacement
        if not valid:
            raise AccessDenied()
        return self.browse(_id)

    def local_impersonate(self):
        """Local impersonate for dev mode"""
        self.ensure_one()
        if not self.env.user._is_admin():
            raise AccessDenied(_("Only admin can impersonate locally"))

        if not hasattr(request, "future_response"):
            raise UserError(
                _("Please install base_future_response for local impersonate to work")
            )
        self._set_auth_cookie(request.future_response)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Impersonation successful"),
                "message": _("You are now impersonating %s\n%%s") % self.login,
                "links": [
                    {
                        "label": f"{endpoint.app.title()} api docs",
                        "url": endpoint.docs_url,
                    }
                    for endpoint in self.directory_id.fastapi_endpoint_ids
                ],
                "type": "success",
                "sticky": False,
            },
        }

    def impersonate(self):
        self.ensure_one()
        if self.env.user not in self.impersonating_user_ids:
            raise AccessDenied(_("You are not allowed to impersonate this user"))

        endpoint_id = self.env.context.get("fastapi_endpoint_id")
        if endpoint_id:
            endpoint = self.env["fastapi.endpoint"].browse(endpoint_id)
            if not endpoint:
                return
        else:
            endpoints = self.directory_id.fastapi_endpoint_ids
            if len(endpoints) == 1:
                endpoint = endpoints
            else:
                wizard = self.env["ir.actions.act_window"]._for_xml_id(
                    "fastapi_auth_partner.fastapi_auth_partner_action_impersonate"
                )
                wizard["context"] = {"default_fastapi_auth_partner_id": self.id}
                return wizard

        base = endpoint.public_url or (
            self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            + endpoint.root_path
        )

        token = random_token()
        expiration = datetime.now() + timedelta(
            minutes=self.directory_id.impersonating_token_duration
        )
        self.write(
            {
                "token_impersonating_encrypted": self._encrypt_token(token),
                "token_impersonating_expiration": expiration,
            }
        )
        url = f"{base}/auth/impersonate/{self.id}/{token}"
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "self",
        }

    @api.depends_context("uid")
    def _compute_user_can_impersonate(self):
        for record in self:
            record.user_can_impersonate = self.env.user in record.impersonating_user_ids

    def impersonating(self, directory, fastapi_partner_id, token):
        hashed_token = self._encrypt_token(token)
        partner_auth = self.search(
            [
                ("id", "=", fastapi_partner_id),
                ("token_impersonating_encrypted", "=", hashed_token),
                ("directory_id", "=", directory.id),
            ]
        )
        if (
            partner_auth
            and partner_auth.token_impersonating_expiration > datetime.now()
        ):
            return partner_auth
        else:
            raise UserError(_("The token is not valid, please request a new one"))

    def _get_template_request_reset_password(self, directory):
        return directory.request_reset_password_template_id

    def _get_template_invite_set_password(self, directory):
        return directory.invite_set_password_template_id

    def _get_template_invite_validate_email(self, directory):
        return directory.invite_validate_email_template_id

    def _generate_token(self, force_expiration=None):
        expiration = force_expiration or (
            datetime.now()
            + timedelta(minutes=self.directory_id.set_password_token_duration)
        )
        token = random_token()
        self.write(
            {
                "token_set_password_encrypted": self._encrypt_token(token),
                "token_expiration": expiration,
            }
        )
        return token

    def _generate_token_mail_validation(self):
        token = random_token()
        self.write(
            {
                "token_mail_validation_encrypted": self._encrypt_token(token),
            }
        )
        return token

    def _encrypt_token(self, token):
        return DEFAULT_CRYPT_CONTEXT_TOKEN.hash(token)

    def set_password(self, directory, token_set_password, password):
        hashed_token = self._encrypt_token(token_set_password)
        partner_auth = self.search(
            [
                ("token_set_password_encrypted", "=", hashed_token),
                ("directory_id", "=", directory.id),
            ]
        )
        if partner_auth and partner_auth.token_expiration > datetime.now():
            partner_auth.write(
                {
                    "password": password,
                    "token_set_password_encrypted": False,
                    "token_expiration": False,
                    "mail_verified": True,
                }
            )
            return partner_auth
        else:
            raise UserError(_("The token is not valid, please request a new one"))

    def send_reset_password(self, template, force_expiration=None):
        self.ensure_one()
        token = self._generate_token(force_expiration=force_expiration)
        template.sudo().with_context(token=token).send_mail(self.id, force_send=True)
        self.date_last_request_reset_pwd = fields.Datetime.now()
        self.date_last_sucessfull_reset_pwd = None
        self.nbr_pending_reset_sent += 1
        return "Instruction sent by email"

    def send_validation_email(self, template, force_expiration=None):
        self.ensure_one()
        token = self._generate_token_mail_validation()
        template.sudo().with_context(token=token).send_mail(self.id, force_send=True)
        return "Instruction sent by email"

    def request_reset_password(self, directory_id, login):
        # request_reset_password is called from a job so we return the result as a string
        auth = self.search(
            [
                ("directory_id", "=", directory_id),
                ("login", "=", login),
            ]
        )
        if auth:
            directory = self.env["fastapi.auth.directory"].browse(directory_id)
            template = self._get_template_request_reset_password(directory)
            if not template:
                raise UserError(
                    _("Forgotten Password template is missing for directory {}").format(
                        directory.name
                    )
                )
            return auth.send_reset_password(template)
        else:
            return "No Partner Auth found, skip"

    def send_invite(self):
        """Use to send an invitation to the user to set
        his password for the first time"""
        self.ensure_one()
        template = self._get_template_invite_set_password(self.directory_id)
        if not template:
            raise UserError(
                _(
                    "Invitation to Set Password template is missing for directory {}"
                ).format(self.directory_id.name)
            )
        return self.send_reset_password(template)

    def send_registration_invite(self):
        """Use to send an invitation to the user to validate its mail address"""
        self.ensure_one()
        template = self._get_template_invite_validate_email(self.directory_id)
        if not template:
            raise UserError(
                _(
                    "Invitation to Email Validation template is missing for directory {}"
                ).format(self.directory_id.name)
            )
        return self.send_validation_email(template)

    def validate_email(self, directory, token_mail_validation):
        hashed_token = self._encrypt_token(token_mail_validation)
        partner_auth = self.search(
            [
                ("token_mail_validation_encrypted", "=", hashed_token),
                ("directory_id", "=", directory.id),
            ]
        )
        if partner_auth:
            partner_auth.write(
                {
                    "token_mail_validation_encrypted": False,
                    "mail_verified": True,
                }
            )
            return partner_auth
        else:
            raise UserError(_("The token is not valid, please request a new one"))

    def _prepare_cookie_payload(self):
        # use short key to reduce cookie size
        return {
            "did": self.directory_id.id,
            "pid": self.partner_id.id,
        }

    def _prepare_cookie(self):
        secret = self.directory_id.cookie_secret_key
        if not secret:
            raise ValidationError(_("No cookie secret key defined"))
        payload = self._prepare_cookie_payload()
        value = URLSafeTimedSerializer(secret).dumps(payload)
        exp = (
            datetime.utcnow() + timedelta(minutes=self.directory_id.cookie_duration)
        ).timestamp()
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

    def _set_auth_cookie(self, response):
        response.set_cookie(COOKIE_AUTH_NAME, **self._prepare_cookie())
