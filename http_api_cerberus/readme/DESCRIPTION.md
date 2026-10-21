Validate and normalize params and results of `http_api` routes
with [Cerberus](https://docs.python-cerberus.org/) schemas.

Provides:

- `CerberusParam`: an `http_api_dispatcher` param validating input params or results
- `cerberus_to_json`: conversion of Cerberus schemas to JSON schemas,
  used to generate API docs

The behavior is compatible with `base_rest`'s `restapi.CerberusValidator`:
unknown keys are dropped, invalid input gives a 400 error and
invalid output gives a 500 error.
