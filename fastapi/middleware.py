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
from a2wsgi.wsgi_typing import Environ, StartResponse

from .pools import event_loop_pool


class ASGIMiddleware(a2wsgi.ASGIMiddleware):
    def __call__(
        self, environ: Environ, start_response: StartResponse
    ) -> Iterable[bytes]:
        with event_loop_pool.get_event_loop() as loop:
            return ASGIResponder(self.app, loop)(environ, start_response)
