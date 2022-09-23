from odoo.api import Environment
from odoo.http import request


def odoo_env() -> Environment:
    # TODO the env must be retreaved from contextvar to ensure that
    # it's properly shared with the thread runner in aswgi
    yield request.env
