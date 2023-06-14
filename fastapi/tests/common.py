# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
from odoo.api import Environment
from odoo.tests.common import TransactionCase

from ..context import odoo_env_ctx


def set_fastapi_env_ctx(test_class: type[TransactionCase], env: Environment) -> None:
    """
    Set the environment in the FastAPI context.
    This is required to use the Odoo env in a FastAPI endpoint when running tests.
    :param test_class: the test class
    :param env: the environment
    """
    test_class._ctx_token = odoo_env_ctx.set(env)

    @test_class.addClassCleanup
    def reset_fast_api_env_ctx():
        odoo_env_ctx.reset(test_class._ctx_token)
