Technical module providing a generic dispatcher for JSON APIs: routes of type `http_api`.

It takes care of the plumbing common to any API endpoint:

- parse params from the query string and the body (JSON, forms) once
- set the language from the `Accept-Language` header
- validate and convert input params and results via pluggable params
  declared on the route (see `http_api_cerberus` for Cerberus schemas)
- serialize results as JSON (dates as ISO strings, decimals as floats)
- turn exceptions into JSON error responses with proper status codes
- provide hooks to extend each step via standard Odoo inheritance

To declare endpoints on classes that are not controllers (eg: services)
whose routes are generated, see `endpoint_spec`.

The error format and the main behaviors are compatible with `base_rest`
to ease the migration of existing APIs.
