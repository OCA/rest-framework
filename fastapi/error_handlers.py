# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from starlette.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

import odoo

from fastapi import Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException

from .context import odoo_env_ctx

_logger = logging.getLogger(__name__)


def _rollback(request: Request, reason: str) -> None:
    cr = odoo_env_ctx.get().cr
    if cr is not None:
        _logger.debug("rollback on %s", reason)
        cr.rollback()


async def _odoo_user_error_handler(
    request: Request, exc: odoo.exceptions.UserError
) -> JSONResponse:
    _rollback(request, "UserError")
    return await http_exception_handler(
        request, HTTPException(HTTP_400_BAD_REQUEST, exc.args[0])
    )


async def _odoo_access_error_handler(
    request: Request, _exc: odoo.exceptions.AccessError
) -> JSONResponse:
    _rollback(request, "AccessError")
    return await http_exception_handler(
        request, HTTPException(HTTP_403_FORBIDDEN, "AccessError")
    )


async def _odoo_missing_error_handler(
    request: Request, _exc: odoo.exceptions.MissingError
) -> JSONResponse:
    _rollback(request, "MissingError")
    return await http_exception_handler(
        request, HTTPException(HTTP_404_NOT_FOUND, "MissingError")
    )


async def _odoo_validation_error_handler(
    request: Request, exc: odoo.exceptions.ValidationError
) -> JSONResponse:
    _rollback(request, "ValidationError")
    return await http_exception_handler(
        request, HTTPException(HTTP_400_BAD_REQUEST, exc.args[0])
    )


async def _odoo_http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    _rollback(request, "HTTPException")
    return await http_exception_handler(request, exc)


async def _odoo_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    _rollback(request, "Exception")
    _logger.exception("Unhandled exception", exc_info=exc)
    return await http_exception_handler(
        request, HTTPException(HTTP_500_INTERNAL_SERVER_ERROR, str(exc))
    )
