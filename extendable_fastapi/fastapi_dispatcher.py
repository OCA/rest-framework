# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from contextlib import contextmanager

from odoo.addons.extendable.registry import _extendable_registries_database
from odoo.addons.fastapi.fastapi_dispatcher import (
    FastApiDispatcher as BaseFastApiDispatcher,
)

from extendable import context


class FastApiDispatcher(BaseFastApiDispatcher):
    routing_type = "fastapi"

    def dispatch(self, endpoint, args):
        with self._manage_extendable_context():
            return super().dispatch(endpoint, args)

    @contextmanager
    def _manage_extendable_context(self):
        env = self.request.env
        registry = _extendable_registries_database.get(env.cr.dbname, {})
        token = context.extendable_registry.set(registry)
        try:
            response = yield
        finally:
            context.extendable_registry.reset(token)
        return response
