# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from starlette import status
from starlette.exceptions import HTTPException, WebSocketException
from starlette.middleware.errors import ServerErrorMiddleware
from starlette.middleware.exceptions import ExceptionMiddleware
from starlette.responses import JSONResponse
from starlette.websockets import WebSocket
from werkzeug.exceptions import HTTPException as WerkzeugHTTPException

from odoo.exceptions import AccessDenied, AccessError, MissingError, UserError

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError, WebSocketRequestValidationError
from fastapi.utils import is_body_allowed_for_status_code


def convert_exception_to_status_body(exc: Exception) -> tuple[int, dict]:
    body = {}
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    details = "Internal Server Error"

    if isinstance(exc, WerkzeugHTTPException):
        status_code = exc.code
        details = exc.description
    elif isinstance(exc, HTTPException):
        status_code = exc.status_code
        details = exc.detail
    elif isinstance(exc, RequestValidationError):
        # Use integer status code to supress starlette >= 0.48 deprecation warning
        # See: https://github.com/fastapi/fastapi/pull/14077
        # status_code = status.HTTP_422_UNPROCESSABLE_CONTENT
        status_code = 422
        details = jsonable_encoder(exc.errors())
    elif isinstance(exc, WebSocketRequestValidationError):
        status_code = status.WS_1008_POLICY_VIOLATION
        details = jsonable_encoder(exc.errors())
    elif isinstance(exc, AccessDenied | AccessError):
        status_code = status.HTTP_403_FORBIDDEN
        details = "AccessError"
    elif isinstance(exc, MissingError):
        status_code = status.HTTP_404_NOT_FOUND
        details = "MissingError"
    elif isinstance(exc, UserError):
        status_code = status.HTTP_400_BAD_REQUEST
        details = exc.args[0]

    if is_body_allowed_for_status_code(status_code):
        # use the same format as in
        # fastapi.exception_handlers.http_exception_handler
        body = {"detail": details}
    return status_code, body


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
