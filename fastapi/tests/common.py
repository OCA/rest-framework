# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
import logging
from collections.abc import Callable
from contextlib import contextmanager
from functools import partial
from typing import Any

from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from odoo.api import Environment
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.base.models.res_users import Users

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from ..context import odoo_env_ctx
from ..dependencies import (
    authenticated_partner_impl,
    optionally_authenticated_partner_impl,
)
from ..error_handlers import convert_exception_to_status_body

_logger = logging.getLogger(__name__)


def default_exception_handler(request: Request, exc: Exception) -> Response:
    """
    Default exception handler that returns a response with the exception details.
    """
    status_code, body = convert_exception_to_status_body(exc)

    if status_code == status.HTTP_500_INTERNAL_SERVER_ERROR:
        # In testing we want to see the exception details of 500 errors
        _logger.error("[%d] Error occurred: %s", exc_info=exc)

    return JSONResponse(
        status_code=status_code,
        content=body,
    )


@tagged("post_install", "-at_install")
class FastAPITransactionCase(TransactionCase):
    """
    This class is a base class for FastAPI tests.

    It defines default values for the attributes used to create the test client.
    The default values can be overridden by setting the corresponding class attributes.
    Default attributes are:
    - default_fastapi_app: the FastAPI app to use to create the test client
    - default_fastapi_router: the FastAPI router to use to create the test client
    - default_fastapi_odoo_env: the Odoo environment that will be used to run
      the endpoint implementation
    - default_fastapi_running_user: the user that will be used to run the endpoint
      implementation
    - default_fastapi_authenticated_partner: the partner that will be used to run
      to build the authenticated_partner and authenticated_partner_env dependencies
    - default_fastapi_dependency_overrides: a dict of dependency overrides that will
        be applied to the app when creating the test client

    The test client is created by calling the _create_test_client method. When
    calling this method, the default values are used unless they are overridden by
    passing the corresponding arguments.

    Even if you can provide a default value for the default_fastapi_app and
    default_fastapi_router attributes, you should always provide only one of them.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.default_fastapi_app: FastAPI | None = None
        cls.default_fastapi_router: APIRouter | None = None
        cls.default_fastapi_odoo_env: Environment = cls.env
        cls.default_fastapi_running_user: Users | None = None
        cls.default_fastapi_authenticated_partner: Partner | None = None
        cls.default_fastapi_dependency_overrides: dict[
            Callable[..., Any], Callable[..., Any]
        ] = {}

    @contextmanager
    def _create_test_client(
        self,
        app: FastAPI | None = None,
        router: APIRouter | None = None,
        user: Users | None = None,
        partner: Partner | None = None,
        env: Environment = None,
        dependency_overrides: dict[Callable[..., Any], Callable[..., Any]] = None,
        raise_server_exceptions: bool = True,
        testclient_kwargs=None,
    ):
        """
        Create a test client for the given app or router.

        This method is a context manager that yields the test client. It
        ensures that the Odoo environment is properly set up when running
        the endpoint implementation, and cleaned up after the test client is
        closed.

        Pay attention to the **'raise_server_exceptions'** argument. It's
        default value is **True**. This means that if the endpoint implementation
        raises an exception, the test client will raise it. That also means
        that if you app includes specific exception handlers, they will not
        be called. If you want to test your exception handlers, you should
        set this argument to **False**. In this case, the test client will
        not raise the exception, but will return it in the response and the
        exception handlers will be called.
        """
        env = env or self.default_fastapi_odoo_env
        user = user or self.default_fastapi_running_user
        dependencies = self.default_fastapi_dependency_overrides.copy()
        if dependency_overrides:
            dependencies.update(dependency_overrides)
        if user:
            env = env(user=user)
        partner = (
            partner
            or self.default_fastapi_authenticated_partner
            or self.env["res.partner"]
        )
        if partner and authenticated_partner_impl in dependencies:
            raise ValueError(
                "You cannot provide an override for the authenticated_partner_impl "
                "dependency when creating a test client with a partner."
            )
        if partner or authenticated_partner_impl not in dependencies:
            dependencies[authenticated_partner_impl] = partial(lambda a: a, partner)
        if partner and optionally_authenticated_partner_impl in dependencies:
            raise ValueError(
                "You cannot provide an override for the "
                "optionally_authenticated_partner_impl "
                "dependency when creating a test client with a partner."
            )
        if partner or optionally_authenticated_partner_impl not in dependencies:
            dependencies[optionally_authenticated_partner_impl] = partial(
                lambda a: a, partner
            )
        app = app or self.default_fastapi_app or FastAPI()
        router = router or self.default_fastapi_router
        if router:
            app.include_router(router)
        app.dependency_overrides = dependencies

        if not raise_server_exceptions:
            # Handle exceptions as in FastAPIDispatcher
            app.exception_handlers.setdefault(Exception, default_exception_handler)

        ctx_token = odoo_env_ctx.set(env)
        testclient_kwargs = testclient_kwargs or {}
        try:
            yield TestClient(
                app,
                raise_server_exceptions=raise_server_exceptions,
                **testclient_kwargs,
            )
        finally:
            odoo_env_ctx.reset(ctx_token)
