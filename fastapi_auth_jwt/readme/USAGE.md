The following FastAPI dependencies are provided and importable from
`odoo.addons.fastapi_auth_jwt.dependencies`:

`def auth_jwt_authenticated_payload() -> Payload`

> Return the authenticated JWT payload. Raise a 401 (unauthorized) if
> absent or invalid.

`def auth_jwt_optionally_authenticated_payload() -> Payload | None`

> Return the authenticated JWT payload, or `None` if the `Authorization`
> header and cookie are absent. Raise a 401 (unauthorized) if present
> and invalid.

`def auth_jwt_authenticated_partner() -> Partner`

> Obtain the authenticated partner corresponding to the provided JWT
> token, according to the partner strategy defined on the `auth_jwt`
> validator. Raise a 401 (unauthorized) if the partner could not be
> determined for any reason.
>
> This is function suitable and intended to override
> `odoo.addons.fastapi.dependencies.authenticated_partner_impl`.
>
> The partner record returned by this function is bound to an
> environment that uses the Odoo user obtained from the user strategy
> defined on the `auth_jwt` validator. When used
> `authenticated_partner_impl` this in turn ensures that
> `odoo.addons.fastapi.dependencies.authenticated_partner_env` is also
> bound to the correct Odoo user.

`def auth_jwt_optionally_authenticated_partner() -> Partner`

> Same as `auth_jwt_partner` except it returns an empty recordset bound
> to the `public` user if the `Authorization` header and cookie are
> absent, or if the JWT validator could not find the partner and
> declares that the partner is not required.

`def auth_jwt_authenticated_odoo_env() -> Environment`

> Return an Odoo environment using the the Odoo user obtained from the
> user strategy defined on the `auth_jwt` validator, if the request
> could be authenticated using a JWT validator. Raise a 401
> (unauthorized) otherwise.
>
> This is function suitable and intended to override
> `odoo.addons.fastapi.dependencies.authenticated_odoo_env_impl`.

`def auth_jwt_default_validator_name() -> str | None`

> Return the name of the default JWT validator to use.
>
> The default implementation returns `None` meaning only one active JWT
> validator is allowed. This dependency is meant to be overridden.

`def auth_jwt_http_header_authorization() -> str | None`

> By default, return the credentials part of the `Authorization` header,
> or `None` if absent. This dependency is meant to be overridden, in
> particular with `fastapi.security.OAuth2AuthorizationCodeBearer` to
> let swagger handle OAuth2 authorization (such override is only
> necessary for comfort when using the swagger interface).
