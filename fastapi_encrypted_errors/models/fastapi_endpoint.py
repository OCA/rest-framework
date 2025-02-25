# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import traceback
import zlib

from cryptography.fernet import Fernet

from odoo import fields, models


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    encrypt_errors = fields.Boolean(
        help="Encrypt errors before sending them to the client.",
    )
    encrypted_errors_secret_key = fields.Char(
        help="The secret key used to encrypt errors before sending them to the client.",
        default=lambda _: Fernet.generate_key(),
        readonly=True,
    )

    def action_generate_encrypted_errors_secret_key(self):
        for record in self:
            record.encrypted_errors_secret_key = Fernet.generate_key()

    def _encrypt_error(self, exc):
        self.ensure_one()
        if not self.encrypt_errors or not self.encrypted_errors_secret_key:
            return

        # Get full traceback
        error = "".join(traceback.format_exception(exc))
        # zlib compression works quite well on tracebacks
        error = zlib.compress(error.encode("utf-8"))
        f = Fernet(self.encrypted_errors_secret_key)
        return f.encrypt(error)

    def _decrypt_error(self, error):
        self.ensure_one()
        if not self.encrypt_errors or not self.encrypted_errors_secret_key:
            return

        f = Fernet(self.encrypted_errors_secret_key)
        error = f.decrypt(error)
        return zlib.decompress(error).decode("utf-8")
