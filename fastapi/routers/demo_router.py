# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
"""
The demo router is a router that demonstrates how to use the fastapi
integration with odoo.
"""
from typing import Annotated

from psycopg2 import errorcodes
from psycopg2.errors import OperationalError

from odoo.api import Environment
from odoo.exceptions import AccessError, MissingError, UserError, ValidationError
from odoo.service.model import MAX_TRIES_ON_CONCURRENCY_FAILURE

from odoo.addons.base.models.res_partner import Partner

from fastapi import APIRouter, Depends, File, HTTPException, Query, status
from fastapi.responses import JSONResponse

from ..dependencies import authenticated_partner, fastapi_endpoint, odoo_env
from ..models import FastapiEndpoint
from ..schemas import DemoEndpointAppInfo, DemoExceptionType, DemoUserInfo

router = APIRouter(tags=["demo"])


@router.get("/demo")
async def hello_word():
    """Hello World!"""
    return {"Hello": "World"}


@router.get("/demo/exception")
async def exception(exception_type: DemoExceptionType, error_message: str):
    """Raise an exception

    This method is used in the test suite to check that any exception
    is correctly handled by the fastapi endpoint and that the transaction
    is roll backed.
    """
    exception_classes = {
        DemoExceptionType.user_error: UserError,
        DemoExceptionType.validation_error: ValidationError,
        DemoExceptionType.access_error: AccessError,
        DemoExceptionType.missing_error: MissingError,
        DemoExceptionType.http_exception: HTTPException,
        DemoExceptionType.bare_exception: NotImplementedError,
    }
    exception_cls = exception_classes[exception_type]
    if exception_cls is HTTPException:
        raise exception_cls(status_code=status.HTTP_409_CONFLICT, detail=error_message)
    raise exception_classes[exception_type](error_message)


@router.get("/demo/lang")
async def get_lang(env: Annotated[Environment, Depends(odoo_env)]):
    """Returns the language according to the available languages in Odoo and the
    Accept-Language header.

    This method is used in the test suite to check that the language is correctly
    set in the Odoo environment according to the Accept-Language header
    """
    return env.context.get("lang")


@router.get("/demo/who_ami")
async def who_ami(
    partner: Annotated[Partner, Depends(authenticated_partner)]
) -> DemoUserInfo:
    """Who am I?

    Returns the authenticated partner
    """
    # This method show you how you can rget the authenticated partner without
    # depending on a specific implementation.
    return DemoUserInfo(name=partner.name, display_name=partner.display_name)


@router.get(
    "/demo/endpoint_app_info",
    dependencies=[Depends(authenticated_partner)],
)
async def endpoint_app_info(
    endpoint: Annotated[FastapiEndpoint, Depends(fastapi_endpoint)],
) -> DemoEndpointAppInfo:
    """Returns the current endpoint configuration"""
    # This method show you how to get access to current endpoint configuration
    # It also show you how you can specify a dependency to force the security
    # even if the method doesn't require the authenticated partner as parameter
    return DemoEndpointAppInfo.model_validate(endpoint)


_CPT = 0


@router.get("/demo/retrying")
async def retrying(
    nbr_retries: Annotated[int, Query(gt=1, lt=MAX_TRIES_ON_CONCURRENCY_FAILURE)],
) -> int:
    """This method is used in the test suite to check that the retrying
    functionality in case of concurrency error on the database is working
    correctly for retryable exceptions.

    The output will be the number of retries that have been done.

    This method is mainly used to test the retrying functionality
    """
    global _CPT
    if _CPT < nbr_retries:
        _CPT += 1
        raise FakeConcurrentUpdateError("fake error")
    tryno = _CPT
    _CPT = 0
    return tryno


@router.post("/demo/retrying")
async def retrying_post(
    nbr_retries: Annotated[int, Query(gt=1, lt=MAX_TRIES_ON_CONCURRENCY_FAILURE)],
    file: Annotated[bytes, File()],
) -> JSONResponse:
    """This method is used in the test suite to check that the retrying
    functionality in case of concurrency error on the database is working
    correctly for retryable exceptions.

    The output will be the number of retries that have been done.

    This method is mainly used to test the retrying functionality
    """
    global _CPT
    if _CPT < nbr_retries:
        _CPT += 1
        raise FakeConcurrentUpdateError("fake error")
    tryno = _CPT
    _CPT = 0
    return JSONResponse(content={"retries": tryno, "file": file.decode("utf-8")})


class FakeConcurrentUpdateError(OperationalError):
    @property
    def pgcode(self):
        return errorcodes.SERIALIZATION_FAILURE
