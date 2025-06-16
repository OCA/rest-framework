## FastAPI API Key Dependencies

The following FastAPI dependencies are provided and importable from
`odoo.addons.fastapi_auth_apikey.dependencies`:

### `def apikey_authenticated_partner_impl() -> Partner`

Return the authenticated partner based on the provided API key. Raise a
401 (unauthorized) if the API key is invalid or the partner could not be
found. Also validates that the user associated with the API key matches
the endpoint’s expected user, if specified.

### `def apikey_optionally_authenticated_partner_impl() -> Partner | None`

Return the authenticated partner based on the provided API key, or an
empty recordset if the key is valid but doesn't match the expected user.
Returns `None` if authentication fails silently.

### `def apikey_authenticated_partner_env() -> Environment`

Return an Odoo environment bound to the authenticated partner. The
partner must be authenticated using `apikey_authenticated_partner_impl`.
Raise a 401 if authentication fails.

### `def apikey_authenticated_partner() -> Partner`

Return the authenticated partner bound to the correct Odoo environment.
This function uses the partner returned by
`apikey_authenticated_partner_impl` and binds it to the environment
returned by `apikey_authenticated_partner_env`.

### `def apikey_optionally_authenticated_partner_env() -> Environment`

Return an Odoo environment bound to the optionally authenticated
partner, or a default environment if the partner could not be
authenticated.

### `def optionally_authenticated_partner() -> Partner | None`

Return the optionally authenticated partner bound to the appropriate
environment, or `None` if no valid API key was provided.
