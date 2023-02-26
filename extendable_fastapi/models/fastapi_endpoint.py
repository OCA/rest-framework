# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from typing import List

from starlette.middleware import Middleware

from odoo import models

from odoo.addons.extendable.registry import _extendable_registries_database

from extendable import context


class ExtendableContextManagerMiddleware(object):
    def __init__(self, app, dbname):
        self.app = app
        self.dbname = dbname

    async def __call__(self, scope, receive, send):
        registry = _extendable_registries_database.get(self.dbname, {})
        token = context.extendable_registry.set(registry)
        try:
            response = await self.app(scope, receive, send)
        finally:
            context.extendable_registry.reset(token)
        return response


class FastapiEndpoint(models.Model):

    _inherit = "fastapi.endpoint"

    def _get_fastapi_app_middlewares(self) -> List[Middleware]:
        middlewares = super()._get_fastapi_app_middlewares()
        middlewares.append(
            (ExtendableContextManagerMiddleware, {"dbname": self.env.cr.dbname})
        )
        return middlewares
