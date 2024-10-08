# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

import passlib

from odoo import _, api, fields, models
from odoo.exceptions import AccessDenied

# please read passlib great documentation
# https://passlib.readthedocs.io
# https://passlib.readthedocs.io/en/stable/narr/quickstart.html#choosing-a-hash
# be carefull odoo requirements use an old version of passlib
DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(["pbkdf2_sha512"])

_logger = logging.getLogger(__name__)


class AuthPartner(models.Model):
    _name = "auth.partner"
    _description = "Auth Partner"
    _rec_name = "login"

    partner_id = fields.Many2one(
        "res.partner", "Partner", required=True, ondelete="cascade", index=True
    )
    directory_id = fields.Many2one(
        "auth.directory", "Directory", required=True, index=True
    )
    user_can_impersonate = fields.Boolean(
        compute="_compute_user_can_impersonate",
        help="Technical field to check if the user can impersonate",
    )
    impersonating_user_ids = fields.Many2many(
        related="directory_id.impersonating_user_ids",
    )
    login = fields.Char(
        compute="_compute_login",
        store=True,
        required=True,
        index=True,
        precompute=True,
    )
    password = fields.Char(compute="_compute_password", inverse="_inverse_password")
    encrypted_password = fields.Char(index=True)
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
    date_last_impersonation = fields.Datetime(
        help="Date of the last sucessfull impersonation"
    )

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
            FROM auth_partner
            WHERE login=%s AND directory_id=%s""",
            (login, directory.id),
        )
        hashed = self.env.cr.fetchone()
        if hashed and hashed[1]:
            # ensure that we have a auth.partner and this partner have a password set
            return hashed
        else:
            raise AccessDenied()

    def _compute_password(self):
        for record in self:
            record.password = ""

    def _inverse_password(self):
        for record in self:
            ctx = record._crypt_context()
            record.encrypted_password = ctx.encrypt(record.password)
            record.password = ""

    def _prepare_partner_auth_signup(self, directory, vals):
        return {
            "login": vals["login"].lower(),
            "password": vals["password"],
            "directory_id": directory.id,
        }

    def _prepare_partner_signup(self, directory, vals):
        return {
            "name": vals["name"],
            "email": vals["login"].lower(),
            "auth_partner_ids": [
                (0, 0, self._prepare_partner_auth_signup(directory, vals))
            ],
        }

    @api.model
    def _signup(self, directory, **kwargs):
        partner = self.env["res.partner"].create(
            [
                self._prepare_partner_signup(directory, kwargs),
            ]
        )
        auth_partner = partner.auth_partner_ids
        directory._send_mail_background(
            "validate_email",
            auth_partner,
            token=auth_partner._generate_validate_email_token(),
        )
        return auth_partner

    @api.model
    def _login(self, directory, login, password, **kwargs):
        self._check_no_empty(login, password)
        login = login.lower()
        try:
            _id, hashed = self._get_hashed_password(directory, login)
            valid, replacement = self._crypt_context().verify_and_update(
                password, hashed
            )

            auth_partner = valid and self.browse(_id)
        except AccessDenied:
            # We do not want to leak information about the login,
            # always raise the same exception
            auth_partner = None

        if not auth_partner:
            raise AccessDenied(_("Invalid Login or Password"))

        if directory.sudo().force_verified_email and not auth_partner.mail_verified:
            raise AccessDenied(
                _(
                    "Email address not validated. Validate your email address by "
                    "clicking on the link in the email sent to you or request a new "
                    "password. "
                )
            )

        if replacement is not None:
            auth_partner.encrypted_password = replacement

        return auth_partner

    @api.model
    def _validate_email(self, directory, token):
        auth_partner = directory._decode_token(token, "validate_email")
        auth_partner.write({"mail_verified": True})
        return auth_partner

    def _get_impersonate_url(self, token, **kwargs):
        # You should override this method according to the impersonation url
        # your framework is using

        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        url = f"{base}/auth/impersonate/{token}"
        return url

    def _get_impersonate_action(self, token, **kwargs):
        return {
            "type": "ir.actions.act_url",
            "url": self._get_impersonate_url(token, **kwargs),
            "target": "new",
        }

    def impersonate(self):
        self.ensure_one()
        if self.env.user not in self.impersonating_user_ids:
            raise AccessDenied(_("You are not allowed to impersonate this user"))

        token = self._generate_impersonating_token()
        return self._get_impersonate_action(token)

    @api.depends_context("uid")
    def _compute_user_can_impersonate(self):
        for record in self:
            record.user_can_impersonate = self.env.user in record.impersonating_user_ids

    @api.model
    def _impersonating(self, directory, token):
        partner_auth = directory._decode_token(
            token,
            "impersonating",
            key_salt=lambda auth_partner: (
                auth_partner.date_last_impersonation.isoformat()
                if auth_partner.date_last_impersonation
                else "never"
            ),
        )
        partner_auth.date_last_impersonation = fields.Datetime.now()
        return partner_auth

    def _on_reset_password_sent(self):
        self.ensure_one()
        self.date_last_request_reset_pwd = fields.Datetime.now()
        self.date_last_sucessfull_reset_pwd = None
        self.nbr_pending_reset_sent += 1

    def _send_invite(self):
        self.ensure_one()
        self.directory_id._send_mail_background(
            "set_password",
            self,
            callback_job=self.delayable()._on_reset_password_sent(),
            token=self._generate_set_password_token(),
        )

    def send_invite(self):
        for rec in self:
            rec._send_invite()

    def _request_reset_password(self):
        return self.directory_id._send_mail_background(
            "reset_password",
            self,
            callback_job=self.delayable()._on_reset_password_sent(),
            token=self._generate_set_password_token(),
        )

    def _set_password(self, directory, token, password):
        auth_partner = directory._decode_token(
            token,
            "set_password",
            key_salt=lambda auth_partner: auth_partner.encrypted_password or "empty",
        )
        auth_partner.write(
            {
                "password": password,
                "mail_verified": True,
            }
        )
        auth_partner.date_last_sucessfull_reset_pwd = fields.Datetime.now()
        auth_partner.nbr_pending_reset_sent = 0
        return auth_partner

    def _generate_set_password_token(self, expiration_delta=None):
        return self.directory_id._generate_token(
            "set_password",
            self,
            expiration_delta
            or timedelta(minutes=self.directory_id.set_password_token_duration),
            key_salt=self.encrypted_password or "empty",
        )

    def _generate_validate_email_token(self):
        return self.directory_id._generate_token(
            # 30 days seem to be a good value, no need for configuration
            "validate_email",
            self,
            timedelta(days=30),
        )

    def _generate_impersonating_token(self):
        return self.directory_id._generate_token(
            "impersonating",
            self,
            timedelta(minutes=self.directory_id.impersonating_token_duration),
            key_salt=(
                self.date_last_impersonation.isoformat()
                if self.date_last_impersonation
                else "never"
            ),
        )
