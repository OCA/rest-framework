# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import abc


class ApiParam(abc.ABC):
    """Convert and validate one side of an endpoint, and describe it.

    Instances are set on the routing of an endpoint
    as `input` (request params) or `output` (endpoint result).

    `call` is duck-typed: it must expose `env`.
    The dispatcher passes the current `ApiCall`,
    API docs builders pass their own object
    and other frameworks can pass their own objects (eg: a service).
    """

    @abc.abstractmethod
    def from_params(self, call):
        """Return the params to pass to the endpoint.

        `call` is the `ApiCall`: read `call.params` for the merged params,
        or `call.query` / `call.body` when only one source is needed,
        so that the other one is never parsed.

        Return a `dict` to pass them as keyword arguments,
        any other value is passed as a single keyword argument
        (see `input_kwarg` routing key).

        Raise `ApiValidationError` if params are not valid.
        """

    @abc.abstractmethod
    def to_response(self, call, result):
        """Return the result to serialize.

        Raise an exception if the result is not valid.
        """

    def to_json_schema(self, call, direction):
        """Return the JSON schema of the param.

        :param direction: "input" or "output"
        :return: a dict or None if the schema is not known
        """
        return None
