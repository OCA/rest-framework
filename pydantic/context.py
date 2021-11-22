# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

# define context vars to hold the pydantic registry

from contextvars import ContextVar

odoo_pydantic_registry = ContextVar("pydantic_registry")
