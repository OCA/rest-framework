## Controllers

Use the `http_api` type on standard routes.
Extra routing keys drive the behavior of the dispatcher:

    from odoo import http
    from odoo.addons.http_api_cerberus.params import CerberusParam

    class PartnerAPI(http.Controller):

        @http.route(
            "/api/partner/<int:id>",
            type="http_api",
            auth="user",
            methods=["GET"],
            output=CerberusParam({"id": {"type": "integer"}, "name": {"type": "string"}}),
        )
        def get(self, id):
            partner = http.request.env["res.partner"].browse(id)
            return {"id": partner.id, "name": partner.name}

Any value returned by the endpoint is serialized as JSON,
unless it's already a response (eg: `request.make_response`).

Routing keys:

| Key | Meaning |
|---|---|
| `input` | `ApiParam` validating and converting request params |
| `input_kwarg` | keyword used to pass non-dict input values (default `payload`) |
| `output` | `ApiParam` validating and converting the result |
| `prepare` | callable or list of callables receiving the `ApiCall`, run before input validation (eg: check headers, update the context) |
| `body_parsers` | `{mimetype: callable}` overriding body parsers |
| `query_parser` | callable overriding the query string parser |
| `error_map` | `[(exception classes, HTTP exception class, include description)]` evaluated before the default error mapping |
| `json_encoder` | `json.JSONEncoder` subclass for the response |
| `csrf` | as for any Odoo route (default `True`). The token is read from the `X-CSRF-Token` header, else from the `csrf_token` param of the query or the body. Set it to `False` for token based APIs |

Params from the URL (eg: `<int:id>`) always win over query and body params.
The query string and the body are parsed on first access.
An `input` param reading only the query or the body keeps the other one unparsed.

## Params

Subclass `odoo.addons.http_api_dispatcher.params.ApiParam`
and implement `from_params`, `to_response` and optionally `to_json_schema`
(used to generate API docs).
Raise `odoo.addons.http_api_dispatcher.errors.ApiValidationError` for invalid input:
the details of the errors are returned in the `errors` key of the response.

## Errors

| Exception | Status | Description in body |
|---|---|---|
| `SessionExpiredException` | 401 | no |
| `MissingError` | 404 | no |
| `AccessError`, `AccessDenied` | 403 | no |
| `UserError`, `ValidationError` | 400 | yes |
| werkzeug `HTTPException` | its own code | yes for 4xx |
| anything else | 500 | no |

The body looks like `{"code": 400, "name": "Bad Request", "description": "..."}`
plus the content of the `rest_json_info` attribute of the exception, if any.

## Hooks

Each step of the pipeline is a classmethod of `ir.http` that can be extended:

- `_http_api_prepare(call)`
- `_http_api_validate_input(call)`
- `_http_api_call(call)`: wrap it to log or profile calls
- `_http_api_validate_output(call)`
- `_http_api_make_response(call)`

All of them receive an `ApiCall` holding the request, the endpoint,
the result and an `extra` dict for your own data.
The params are exposed lazily: `call.query`, `call.body` and `call.params`
(the merged dict, built on first access).
