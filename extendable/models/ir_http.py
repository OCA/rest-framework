# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from contextlib import contextmanager

from odoo import models
from odoo.http import request

from extendable import context

from ..registry import _extendable_registries_database


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls, endpoint):
        with cls._extendable_context_registry():
            return super()._dispatch(endpoint)

    @classmethod
    @contextmanager
    def _extendable_context_registry(cls):
        registry = _extendable_registries_database.get(request.env.cr.dbname, {})
        token = context.extendable_registry.set(registry)
        try:
            yield
        finally:
            context.extendable_registry.reset(token)
