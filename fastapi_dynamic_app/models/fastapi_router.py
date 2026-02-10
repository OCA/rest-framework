# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import sys

from odoo import api, fields, models

from fastapi import APIRouter


class FastapiRouter(models.Model):
    _name = "fastapi.router"
    _description = "FastAPI Router for dynamic endpoints"

    name = fields.Char(required=True)
    module = fields.Char(required=True)
    active = fields.Boolean(default=True)
    display_name = fields.Char(compute="_compute_display_name")

    _sql_constraints = [
        ("name_module_unique", "unique(name, module)", "Router already exists")
    ]

    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{re.sub(r'_router', '', rec.name)} ({rec.module})"

    def _get_loaded_routers(self):
        loaded_modules = self.env["ir.module.module"].search(
            [("state", "=", "installed")]
        )
        for module in loaded_modules:
            mod_name = f"odoo.addons.{module.name}"
            if mod_name not in sys.modules:
                continue
            mod = sys.modules[mod_name]
            if hasattr(mod, "routers"):
                for var in dir(mod.routers):
                    value = getattr(mod.routers, var)
                    if isinstance(value, APIRouter):
                        yield (module.name, var)

    @api.model
    def sync(self):
        routers = self.env["fastapi.router"].with_context(active_test=False).search([])

        current_routers = self.env["fastapi.router"]

        for module, name in self._get_loaded_routers():
            router = routers.filtered(
                lambda r, n=name, m=module: r.name == n and r.module == m
            )
            if not router:
                router = self.create({"name": name, "module": module})
            elif not router.active:
                router.active = True

            current_routers |= router

        (routers - current_routers).write({"active": False})

    def _get_router(self):
        return getattr(sys.modules[f"odoo.addons.{self.module}"].routers, self.name)
