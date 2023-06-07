# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

# define context vars to hold the odoo env

from contextvars import ContextVar

from odoo.api import Environment

odoo_env_ctx: ContextVar[Environment] = ContextVar("odoo_env_ctx")
