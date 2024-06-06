# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from starlette.exceptions import WebSocketException
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket

from fastapi import Request

# we need to monkey patch the ServerErrorMiddleware and ExceptionMiddleware classes
# to ensure that all the exceptions that are handled by these specific
# middlewares are let to bubble up to the retrying mechanism and the
# dispatcher error handler to ensure that appropriate action are taken
# regarding the transaction, environment, and registry. These middlewares
# are added by default by FastAPI when creating an application and it's not
# possible to remove them. So we need to monkey patch them.


def pass_through_exception_handler(
    self, request: Request, exc: Exception
) -> JSONResponse:
    raise exc


def pass_through_websocket_exception_handler(
    self, websocket: WebSocket, exc: WebSocketException
) -> None:
    raise exc


ServerErrorMiddleware.error_response = pass_through_exception_handler
ExceptionMiddleware.http_exception = pass_through_exception_handler
ExceptionMiddleware.websocket_exception = pass_through_websocket_exception_handler
