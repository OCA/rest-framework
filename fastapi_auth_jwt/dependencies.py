# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from typing import Annotated, Any, Dict, Optional, Tuple, Union

from starlette.status import HTTP_401_UNAUTHORIZED

from odoo.api import Environment

from odoo.addons.auth_jwt.exceptions import (
    ConfigurationError,
    Unauthorized,
    UnauthorizedCompositeJwtError,
    UnauthorizedMissingAuthorizationHeader,
    UnauthorizedMissingCookie,
)
from odoo.addons.auth_jwt.models.auth_jwt_validator import AuthJwtValidator
from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import odoo_env

from fastapi import Depends, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_logger = logging.getLogger(__name__)


Payload = Dict[str, Any]


def _get_auth_jwt_validator(
    validator_name: Union[str, None],
    env: Environment,
) -> AuthJwtValidator:
    validator = env["auth.jwt.validator"].sudo()._get_validator_by_name(validator_name)
    assert len(validator) == 1
    return validator


def _request_has_authentication(
    request: Request,
    authorization_credentials: Optional[HTTPAuthorizationCredentials],
    validator: AuthJwtValidator,
) -> Union[Payload, None]:
    if authorization_credentials is not None:
        return True
    if not validator.cookie_enabled:
        # no Authorization header and cookies not enabled
        return False
    return request.cookies.get(validator.cookie_name) is not None


def _get_jwt_payload(
    request: Request,
    authorization_header: Optional[HTTPAuthorizationCredentials],
    validator: AuthJwtValidator,
) -> Payload:
    """Obtain and validate the JWT payload from the request authorization header or
    cookie (if enabled on the validator)."""
    if authorization_header is not None:
        return validator._decode(authorization_header.credentials)
    if not validator.cookie_enabled:
        _logger.info("Missing or malformed authorization header.")
        raise UnauthorizedMissingAuthorizationHeader()
    assert validator.cookie_name
    cookie_token = request.cookies.get(validator.cookie_name)
    if not cookie_token:
        _logger.info("Missing authorization cookie %s.", validator.cookie_name)
        raise UnauthorizedMissingCookie()
    return validator._decode(cookie_token, secret=validator._get_jwt_cookie_secret())


def _get_jwt_payload_and_validator(
    request: Request,
    response: Response,
    authorization_header: Optional[HTTPAuthorizationCredentials],
    validator: AuthJwtValidator,
) -> Tuple[Payload, AuthJwtValidator]:
    try:
        payload = None
        exceptions = {}
        while validator:
            try:
                payload = _get_jwt_payload(request, authorization_header, validator)
                break
            except Unauthorized as e:
                exceptions[validator.name] = e
                validator = validator.next_validator_id

        if not payload:
            if len(exceptions) == 1:
                raise list(exceptions.values())[0]
            raise UnauthorizedCompositeJwtError(exceptions)

        if validator.cookie_enabled:
            if not validator.cookie_name:
                _logger.info("Cookie name not set for validator %s", validator.name)
                raise ConfigurationError()
            response.set_cookie(
                key=validator.cookie_name,
                value=validator._encode(
                    payload,
                    secret=validator._get_jwt_cookie_secret(),
                    expire=validator.cookie_max_age,
                ),
                max_age=validator.cookie_max_age,
                path=validator.cookie_path or "/",
                secure=validator.cookie_secure,
                httponly=True,
            )

        return payload, validator
    except Unauthorized as e:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED) from e


def auth_jwt_default_validator_name() -> Union[str, None]:
    return None


class BaseAuthJwt:  # noqa: B903
    def __init__(
        self, validator_name: Optional[str] = None, allow_unauthenticated: bool = False
    ):
        self.validator_name = validator_name
        self.allow_unauthenticated = allow_unauthenticated


class AuthJwtPayload(BaseAuthJwt):
    def __call__(
        self,
        request: Request,
        response: Response,
        authorization_header: Annotated[
            Optional[HTTPAuthorizationCredentials],
            Depends(HTTPBearer(auto_error=False)),
        ],
        default_validator_name: Annotated[
            Union[str, None],
            Depends(auth_jwt_default_validator_name),
        ],
        env: Annotated[
            Environment,
            Depends(odoo_env),
        ],
    ) -> Optional[Payload]:
        validator = _get_auth_jwt_validator(
            self.validator_name or default_validator_name, env
        )
        if self.allow_unauthenticated and not _request_has_authentication(
            request, authorization_header, validator
        ):
            return None
        return _get_jwt_payload_and_validator(
            request, response, authorization_header, validator
        )[0]


class AuthJwtPartner(BaseAuthJwt):
    def __call__(
        self,
        request: Request,
        response: Response,
        authorization_header: Annotated[
            Optional[HTTPAuthorizationCredentials],
            Depends(HTTPBearer(auto_error=False)),
        ],
        default_validator_name: Annotated[
            Union[str, None],
            Depends(auth_jwt_default_validator_name),
        ],
        env: Annotated[
            Environment,
            Depends(odoo_env),
        ],
    ) -> Partner:
        validator = _get_auth_jwt_validator(
            self.validator_name or default_validator_name, env
        )
        if self.allow_unauthenticated and not _request_has_authentication(
            request, authorization_header, validator
        ):
            return env["res.partner"].with_user(env.ref("base.public_user")).browse()
        payload, validator = _get_jwt_payload_and_validator(
            request, response, authorization_header, validator
        )
        try:
            uid = validator._get_and_check_uid(payload)
            partner_id = validator._get_and_check_partner_id(payload)
        except Unauthorized as e:
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED) from e
        if not partner_id:
            _logger.info("Could not determine partner from JWT payload.")
            raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)
        return env["res.partner"].with_user(uid).browse(partner_id)


class AuthJwtOdooEnv(BaseAuthJwt):
    def __call__(
        self,
        request: Request,
        response: Response,
        authorization_header: Annotated[
            Optional[HTTPAuthorizationCredentials],
            Depends(HTTPBearer(auto_error=False)),
        ],
        default_validator_name: Annotated[
            Union[str, None],
            Depends(auth_jwt_default_validator_name),
        ],
        env: Annotated[
            Environment,
            Depends(odoo_env),
        ],
    ) -> Environment:
        validator = _get_auth_jwt_validator(
            self.validator_name or default_validator_name, env
        )
        payload, validator = _get_jwt_payload_and_validator(
            request, response, authorization_header, validator
        )
        uid = validator._get_and_check_uid(payload)
        return odoo_env(user=uid)


auth_jwt_authenticated_payload = AuthJwtPayload()

auth_jwt_optionally_authenticated_payload = AuthJwtPayload(allow_unauthenticated=True)

auth_jwt_authenticated_partner = AuthJwtPartner()

auth_jwt_optionally_authenticated_partner = AuthJwtPartner(allow_unauthenticated=True)

auth_jwt_authenticated_odoo_env = AuthJwtOdooEnv()
