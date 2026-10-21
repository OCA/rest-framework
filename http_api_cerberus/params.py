# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Cerberus params for `http_api` routes.

Heavily inspired by `CerberusValidator` and `CerberusListValidator`
in `base_rest.restapi` (OCA/rest-framework): same validation behavior,
same error messages.
"""

import logging

from cerberus import Validator

from odoo.addons.http_api_dispatcher.errors import ApiValidationError
from odoo.addons.http_api_dispatcher.params import ApiParam

from .tools import cerberus_to_json

_logger = logging.getLogger(__name__)


class CerberusParam(ApiParam):
    """Validate and normalize data with a Cerberus schema.

    :param schema: the Cerberus schema, as:

        * a dict
        * a `cerberus.Validator` instance (not thread-safe: prefer a dict)
        * a callable `(call, direction) -> schema`
        * a string: name of a method returning the schema,
          looked up on the owner of the endpoint (see `_get_schema_owner`)

    :param purge_unknown: drop keys not declared in the schema
    :param validator_cls: `cerberus.Validator` subclass to use
        (eg: to provide custom rules or coercers)
    :param as_list: data is a list of items matching the schema
    :param min_items: minimum number of items (list only)
    :param max_items: maximum number of items (list only)
    :param unique_items: documentation only (list only)
    :param cache: cache the resolved schema (per database and direction).
        Use it only when the schema does not depend on the request.
    :param strict_output: raise on invalid results.
        If False, invalid results are logged and returned as they are.
    """

    def __init__(
        self,
        schema,
        *,
        purge_unknown=True,
        validator_cls=None,
        as_list=False,
        min_items=None,
        max_items=None,
        unique_items=None,
        cache=False,
        strict_output=True,
    ):
        """Store the options: the schema is resolved lazily, per call."""
        self.schema = schema
        self.purge_unknown = purge_unknown
        self.validator_cls = validator_cls or Validator
        self.as_list = as_list
        self.min_items = min_items
        self.max_items = max_items
        self.unique_items = unique_items
        self.cache = cache
        self.strict_output = strict_output
        self._schema_cache = {}

    def __repr__(self):
        """Show the schema to ease debugging of routes."""
        return f"<{self.__class__.__name__}: {self.schema!r}>"

    # Schema lookup

    def _get_schema_owner(self, call):
        """Return the object holding schema methods.

        `call.owner` if available (eg: a service),
        otherwise the controller of the endpoint, otherwise `call` itself.
        """
        owner = getattr(call, "owner", None)
        if owner is not None:
            return owner
        endpoint = getattr(call, "endpoint", None)
        func = getattr(endpoint, "func", endpoint)
        return getattr(func, "__self__", call)

    def _resolve_schema(self, call, direction):
        """Turn the declared schema into a Cerberus schema or validator."""
        schema = self.schema
        if isinstance(schema, str):
            schema = getattr(self._get_schema_owner(call), schema)()
        elif callable(schema) and not isinstance(schema, Validator):
            schema = schema(call, direction)
        return schema

    def get_schema(self, call, direction):
        """Return the schema, from the cache if enabled.

        The cache is per database: callables might return db dependent schemas.
        """
        if not self.cache:
            return self._resolve_schema(call, direction)
        key = (call.env.cr.dbname, direction)
        if key not in self._schema_cache:
            self._schema_cache[key] = self._resolve_schema(call, direction)
        return self._schema_cache[key]

    def get_validator(self, call, direction):
        """Return the validator for given direction.

        Dict schemas get a new validator per call:
        validators hold state and are not thread safe.
        """
        schema = self.get_schema(call, direction)
        if isinstance(schema, Validator):
            return schema
        if isinstance(schema, dict):
            return self.validator_cls(schema, purge_unknown=self.purge_unknown)
        raise ValueError(f"Unable to get a Cerberus schema from {self.schema!r}")

    # ApiParam

    def from_params(self, call):
        """Validate and normalize the params of the call."""
        params = call.params
        if self.as_list:
            return self._validate_list(call, params, "input")
        validator = self.get_validator(call, "input")
        if validator.validate(params):
            return validator.document
        raise ApiValidationError(
            call.env._("BadRequest %s", validator.errors), errors=validator.errors
        )

    def to_response(self, call, result):
        """Validate and normalize the result of the endpoint."""
        if self.as_list:
            return self._validate_list(call, result, "output")
        validator = self.get_validator(call, "output")
        if validator.validate(result):
            return validator.document
        return self._invalid_output(call, result, validator.errors)

    def to_json_schema(self, call, direction):
        """Describe the param as JSON schema, for API docs."""
        json_schema = cerberus_to_json(self.get_validator(call, direction).schema)
        if not self.as_list:
            return json_schema
        json_schema = {"type": "array", "items": json_schema}
        if self.min_items is not None:
            json_schema["minItems"] = self.min_items
        if self.max_items is not None:
            json_schema["maxItems"] = self.max_items
        if self.unique_items is not None:
            json_schema["uniqueItems"] = self.unique_items
        return json_schema

    # Helpers

    def _invalid_output(self, call, result, errors):
        """Raise, or only log when output is not strict."""
        if self.strict_output:
            raise SystemError(call.env._("Invalid Response %s", errors))
        _logger.warning("Invalid response (not enforced): %s", errors)
        return result

    def _validate_list(self, call, data, direction):
        """Validate each item and the size of the list, collecting all errors."""
        validator = self.get_validator(call, direction)
        data = data or []
        errors = {}
        values = []
        for idx, item in enumerate(data):
            if validator.validate(item):
                values.append(validator.document)
            else:
                errors[idx] = validator.errors
        count = len(data)
        if self.min_items is not None and count < self.min_items:
            errors["min_items"] = [f"{count} < {self.min_items}"]
        if self.max_items is not None and count > self.max_items:
            errors["max_items"] = [f"{count} > {self.max_items}"]
        if not errors:
            return values
        if direction == "output":
            return self._invalid_output(call, data, errors)
        raise ApiValidationError(call.env._("BadRequest %s", errors), errors=errors)
