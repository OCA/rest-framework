# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from contextlib import contextmanager

from odoo import models
from odoo.http import request

from .context import odoo_pydantic_registry
from .registry import _pydantic_classes_databases


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _dispatch(cls):
        with cls._pydantic_context_registry():
            return super()._dispatch()

    @classmethod
    @contextmanager
    def _pydantic_context_registry(cls):
        registry = _pydantic_classes_databases.get(request.env.cr.dbname, {})
        token = odoo_pydantic_registry.set(registry)
        try:
            yield
        finally:
            odoo_pydantic_registry.reset(token)
