# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models
from odoo.exceptions import AccessDenied
from odoo.http import request

from .directory_auth import COOKIE_AUTH_NAME

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    # Remove this hack in V16
    @classmethod
    def _get_directory_auth(cls):
        raise NotImplementedError()

    @classmethod
    def _auth_method_partner_auth(cls):
        directory = cls._get_directory_auth()
        partner = directory._get_partner_from_request()
        if partner:
            request._env = None
            request.uid = 1
            request.auth_res_partner_id = partner.id
            request.auth_directory_id = directory.id
        else:
            raise AccessDenied()

    @classmethod
    def _auth_method_public_or_partner_auth(cls):
        if request.httprequest.cookies.get(COOKIE_AUTH_NAME):
            try:
                cls._auth_method_partner_auth()
                return
            except Exception:
                pass
        request.uid = 1
