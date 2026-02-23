# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
"""
ASGI middleware for FastAPI.

This module provides an ASGI middleware for FastAPI applications. The middleware
is designed to ensure managed the lifecycle of the threads used to as event loop
for the ASGI application.

"""

from collections.abc import Iterable

import a2wsgi
from a2wsgi.asgi import ASGIResponder
from a2wsgi.asgi_typing import ASGIApp
from a2wsgi.wsgi_typing import Environ, StartResponse

from .pools import event_loop_pool


class ASGIMiddleware(a2wsgi.ASGIMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        wait_time: float | None = None,
    ) -> None:
        # We don't want to use the default event loop policy
        # because we want to manage the event loop ourselves
        # using the event loop pool.
        # Since the the base class check if the given loop is
        # None, we can pass False to avoid the initialization
        # of the default event loop
        super().__init__(app, wait_time, False)

    def __call__(
        self, environ: Environ, start_response: StartResponse
    ) -> Iterable[bytes]:
        with event_loop_pool.get_event_loop() as loop:
            return ASGIResponder(self.app, loop)(environ, start_response)
