from odoo.api import Environment

from .context import odoo_env_ctx


def odoo_env() -> Environment:
    yield odoo_env_ctx.get()
