# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import passlib
import logging
from odoo import api, fields, models
from odoo.exceptions import AccessDenied

# please read passlib great documentation
# https://passlib.readthedocs.io
# https://passlib.readthedocs.io/en/stable/narr/quickstart.html#choosing-a-hash
# be carefull odoo requirements use an old version of passlib
DEFAULT_CRYPT_CONTEXT = passlib.context.CryptContext(['pbkdf2_sha512'])


_logger = logging.getLogger(__name__)


class PartnerAuth(models.Model):
    _name = "partner.auth"
    _description = "Partner Auth"

    partner_id = fields.Many2one(
        'res.partner',
        'Partner')
    directory_id = fields.Many2one(
        'directory.auth',
        'Directory')
    login = fields.Char(compute="_compute_login", store=True)
    password = fields.Char(compute="_compute_password", inverse="_set_password")
    encrypted_password = fields.Char()

    _sql_constraints = [
        (
            'directory_login_uniq',
            'unique (directory_id, login)',
            'Login must be uniq per directory !'
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
                isinstance(password, str) and password
                and isinstance(login, str) and login):
            _logger.warning("Invalid login/password for sign in")
            raise AccessDenied()

    def _get_hashed_password(self, directory, login):
        self.env.cr.execute("""
            SELECT id, COALESCE(encrypted_password, '')
            FROM partner_auth
            WHERE login=%s AND directory_id=%s""",
            (login, directory.id)
        )
        hashed = self.env.cr.fetchone()
        if hashed:
            return hashed
        else:
            raise AccessDenied()

    def _compute_password(self):
        for record in self:
            record.password = ""

    def _set_password(self):
        # TODO add check on group
        for record in self:
            ctx = record._crypt_context()
            record.encrypted_password = ctx.encrypt(record.password)

    @api.model
    def sign_in(self, directory, login, password):
        self._check_no_empty(login, password)
        _id, hashed = self._get_hashed_password(directory, login)
        valid, replacement = self._crypt_context().verify_and_update(password, hashed)

        if replacement is not None:
            self.browse(_id).encrypted_password = replacement

        if not valid:
            raise AccessDenied()
        return self.browse(_id)

#
#    def change_password(self, password):
#        pwd_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()
#        pwd_field = self._authenticable_pwd_hash
#        setattr(self, pwd_field, pwd_hash)
#        return "Success"
#
#    def reset_password(self):
#        pass
#
#    def sign_out(self):
#        pass
#
#
