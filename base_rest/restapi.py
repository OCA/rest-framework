# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import abc
import functools
import json

from cerberus import Validator

from odoo import http
from odoo.exceptions import UserError, ValidationError

from .tools import ROUTING_DECORATOR_ATTR, cerberus_to_json


def method(routes, input_param=None, output_param=None, **kw):
    """Decorator marking the decorated method as being a handler for
      REST requests. The method must be part of a component inheriting from
    ``base.rest.service``.

      :param routes: list of tuple (path, http method). path is a string or
                    array.
                    Each tuple determines which http requests and http method
                    will match the decorated method. The path part can be a
                    single string or an array of strings. See werkzeug's routing
                    documentation for the format of path expression (
                    http://werkzeug.pocoo.org/docs/routing/ ).
      :param: input_param: An instance of an object that implemented
                    ``RestMethodParam``. When processing a request, the http
                    handler first call the from_request method and then call the
                    decorated method with the result of this call.
      :param: output_param: An instance of an object that implemented
                    ``RestMethodParam``. When processing the result of the
                    call to the decorated method, the http handler first call
                    the `to_response` method with this result and then return
                    the result of this call.
      :param auth: The type of authentication method. A special auth method
                   named 'public_or_default' can be used. In such a case
                   when the HTTP route will be generated, the auth method
                   will be computed from the '_default_auth' property defined
                   on the controller with 'public_or_' as prefix.
                   The purpose of 'public_or_default' auth method is to provide
                   a way to specify that a method should work for anonymous users
                   but can be enhanced when an authenticated user is know.
                   It implies that when the 'default' auth part of 'public_or_default'
                   will be replaced by the default_auth specified on the controller
                   in charge of registering the web services, an auth method with
                   the same name is defined into odoo to provide such a behavior.
                   In the following example, the auth method on my ping service
                   will be `public_or_jwt` since this authentication method is
                   provided by the auth_jwt addon.

                    .. code-block:: python

                        class PingService(Component):
                            _inherit = "base.rest.service"
                            _name = "ping_service"
                            _usage = "ping"
                            _collection = "test.api.services"

                            @restapi.method(
                                [(["/<string:message>""], "GET")],
                                auth="public_or_auth",
                            )
                            def _ping(self, message):
                                return {"message": message}


                        class MyRestController(main.RestController):
                            _root_path = '/test/'
                            _collection_name = "test.api.services"
                            _default_auth = "jwt'

      :param cors: The Access-Control-Allow-Origin cors directive value. When
                   set, this automatically adds OPTIONS to allowed http methods
                   so the Odoo request handler will accept it.
      :param bool csrf: Whether CSRF protection should be enabled for the route.
                        Defaults to ``False``
      :param bool save_session: Whether HTTP session should be saved into the
                                session store: Default to ``True``

    """

    def decorator(f):
        _routes = []
        for paths, http_methods in routes:
            if not isinstance(paths, list):
                paths = [paths]
            if not isinstance(http_methods, list):
                http_methods = [http_methods]
            if kw.get("cors") and "OPTIONS" not in http_methods:
                http_methods.append("OPTIONS")
            for m in http_methods:
                _routes.append(([p for p in paths], m))
        routing = {
            "routes": _routes,
            "input_param": input_param,
            "output_param": output_param,
        }
        routing.update(kw)

        @functools.wraps(f)
        def response_wrap(*args, **kw):
            response = f(*args, **kw)
            return response

        setattr(response_wrap, ROUTING_DECORATOR_ATTR, routing)
        response_wrap.original_func = f
        return response_wrap

    return decorator


class RestMethodParam(abc.ABC):
    @abc.abstractmethod
    def from_params(self, service, params):
        """
        This method is called to process the parameters received at the
        controller. This method should validate and sanitize these paramaters.
        It could also be used to transform these parameters into the format
        expected by the called method
        :param service:
        :param request: `HttpRequest.params`
        :return: Value into the format expected by the method
        """

    @abc.abstractmethod
    def to_response(self, service, result) -> http.Response:
        """
        This method is called to prepare the result of the call to the method
        in a format suitable by the controller (http.Response or JSON dict).
        It's responsible for validating and sanitizing the result.
        :param service:
        :param obj:
        :return: http.Response or JSON dict
        """

    @abc.abstractmethod
    def to_openapi_query_parameters(self, service, spec) -> dict:
        return {}

    @abc.abstractmethod
    def to_openapi_requestbody(self, service, spec) -> dict:
        return {}

    @abc.abstractmethod
    def to_openapi_responses(self, service, spec) -> dict:
        return {}

    @abc.abstractmethod
    def to_json_schema(self, service, spec, direction) -> dict:
        return {}


class BinaryData(RestMethodParam):
    def __init__(self, mediatypes="*/*", required=False):
        if not isinstance(mediatypes, list):
            mediatypes = [mediatypes]
        self._mediatypes = mediatypes
        self._required = required

    def to_json_schema(self, service, spec, direction):
        return {
            "type": "string",
            "format": "binary",
            "required": self._required,
        }

    @property
    def _binary_content_schema(self):
        return {
            mediatype: {"schema": self.to_json_schema(None, None, None)}
            for mediatype in self._mediatypes
        }

    def to_openapi_requestbody(self, service, spec):
        return {"content": self._binary_content_schema}

    def to_openapi_query_parameters(self, service, spec):
        raise NotImplementedError(
            "BinaryData are not (?yet?) supported as query paramters"
        )

    def to_openapi_responses(self, service, spec):
        return {"200": {"content": self._binary_content_schema}}

    def to_response(self, service, result):
        if not isinstance(result, http.Response):
            # The response has not been build by the called method...
            result = self._to_http_response(result)
        return result

    def from_params(self, service, params):
        return params

    def _to_http_response(self, result):
        mediatype = self._mediatypes[0] if len(self._mediatypes) == 1 else "*/*"
        headers = [
            ("Content-Type", mediatype),
            ("X-Content-Type-Options", "nosniff"),
            ("Content-Disposition", http.content_disposition("file")),
            ("Content-Length", len(result)),
        ]
        return http.request.make_response(result, headers)


class CerberusValidator(RestMethodParam):
    def __init__(self, schema):
        """

        :param schema: can be dict as cerberus schema, an instance of
                       cerberus.Validator or a sting with the method name to
                       call on the service to get the schema or the validator
        """
        self._schema = schema

    def from_params(self, service, params):
        validator = self.get_cerberus_validator(service, "input")
        if validator.validate(params):
            return validator.document
        raise UserError(service.env._("BadRequest %s") % validator.errors)

    def to_response(self, service, result):
        validator = self.get_cerberus_validator(service, "output")
        if validator.validate(result):
            return validator.document
        raise SystemError(service.env._("Invalid Response %s") % validator.errors)

    def to_openapi_query_parameters(self, service, spec):
        json_schema = self.to_json_schema(service, spec, "input")
        parameters = []
        for prop, spec in list(json_schema["properties"].items()):
            params = {
                "name": prop,
                "in": "query",
                "required": prop in json_schema["required"],
                "allowEmptyValue": spec.get("nullable", False),
                "default": spec.get("default"),
            }
            if spec.get("schema"):
                params["schema"] = spec.get("schema")
            else:
                params["schema"] = {"type": spec["type"]}
            if spec.get("items"):
                params["schema"]["items"] = spec.get("items")
            if "enum" in spec:
                params["schema"]["enum"] = spec["enum"]

            parameters.append(params)

            if spec["type"] == "array":
                # To correctly handle array into the url query string,
                # the name must ends with []
                params["name"] = params["name"] + "[]"

        return parameters

    def to_openapi_requestbody(self, service, spec):
        json_schema = self.to_json_schema(service, spec, "input")
        return {"content": {"application/json": {"schema": json_schema}}}

    def to_openapi_responses(self, service, spec):
        json_schema = self.to_json_schema(service, spec, "output")
        return {"200": {"content": {"application/json": {"schema": json_schema}}}}

    def get_cerberus_validator(self, service, direction):
        assert direction in ("input", "output")
        schema = self._schema
        if isinstance(self._schema, str):
            validator_component = service.component(usage="cerberus.validator")
            schema = validator_component.get_validator_handler(
                service, self._schema, direction
            )()
        if isinstance(schema, Validator):
            return schema
        if isinstance(schema, dict):
            return Validator(schema, purge_unknown=True)
        raise Exception(
            service.env._("Unable to get cerberus schema from %s") % self._schema
        )

    def to_json_schema(self, service, spec, direction):
        schema = self.get_cerberus_validator(service, direction).schema
        return cerberus_to_json(schema)


class CerberusListValidator(CerberusValidator):
    def __init__(self, schema, min_items=None, max_items=None, unique_items=None):
        """
        :param schema: Cerberus list item schema
                       can be dict as cerberus schema, an instance of
                       cerberus.Validator or a sting with the method name to
                       call on the service to get the schema or the validator
        :param min_items: A list instance is valid against "min_items" if its
                          size is greater than, or equal to, min_items.
                          The value MUST be a non-negative integer.
        :param max_items: A list instance is valid against "max_items" if its
                          size is less than, or equal to, max_items.
                          The value MUST be a non-negative integer.
        :param unique_items: Used to document that the list should only
                             contain unique items.
                             (Not enforced at validation time)
        """
        super().__init__(schema=schema)
        self._min_items = min_items
        self._max_items = max_items
        self._unique_items = unique_items

    def from_params(self, service, params):
        return self._do_validate(service, data=params, direction="input")

    def to_response(self, service, result):
        return self._do_validate(service, data=result, direction="output")

    def to_openapi_query_parameters(self, service, spec):
        raise NotImplementedError("List are not (?yet?) supported as query paramters")

    # pylint: disable=W8120,W8115
    def _do_validate(self, service, data, direction):
        validator = self.get_cerberus_validator(service, direction)
        values = []
        ExceptionClass = UserError if direction == "input" else SystemError
        for idx, p in enumerate(data):
            if not validator.validate(p):
                raise ExceptionClass(
                    service.env._(
                        "BadRequest item %(idx)s :%(errors)s",
                        idx=idx,
                        errors=validator.errors,
                    )
                )
            values.append(validator.document)
        if self._min_items is not None and len(values) < self._min_items:
            raise ExceptionClass(
                service.env._(
                    "BadRequest: Not enough items in the list (%(current)s "
                    "< %(expected)s)",
                    current=len(values),
                    expected=self._min_items,
                )
            )
        if self._max_items is not None and len(values) > self._max_items:
            raise ExceptionClass(
                service.env._(
                    "BadRequest: Too many items in the list (%(current)s "
                    "> %(expected)s)",
                    current=len(values),
                    expected=self._max_items,
                )
            )
        return values

    def to_json_schema(self, service, spec, direction):
        cerberus_schema = self.get_cerberus_validator(service, direction).schema
        json_schema = cerberus_to_json(cerberus_schema)
        json_schema = {"type": "array", "items": json_schema}
        if self._min_items is not None:
            json_schema["minItems"] = self._min_items
        if self._max_items is not None:
            json_schema["maxItems"] = self._max_items
        if self._unique_items is not None:
            json_schema["uniqueItems"] = self._unique_items
        return json_schema


class MultipartFormData(RestMethodParam):
    def __init__(self, parts):
        """This allows to create multipart/form-data endpoints.
        :param parts:  list of RestMethodParam
        """
        if not isinstance(parts, dict):
            raise RuntimeError("You must provide a dict of RestMethodParam")
        self._parts = parts

    def to_openapi_properties(self, service, spec, direction):
        properties = {}
        for key, part in self._parts.items():
            properties[key] = part.to_json_schema(service, spec, direction)
        return properties

    def to_openapi_encoding(self):
        encodings = {}
        for key, part in self._parts.items():
            if isinstance(part, BinaryData):
                encodings[key] = {"contentType": ", ".join(part._mediatypes)}
        return encodings

    def to_json_schema(self, service, spec, direction):
        res = {
            "multipart/form-data": {
                "schema": {
                    "type": "object",
                    "properties": self.to_openapi_properties(service, spec, direction),
                }
            }
        }
        encoding = self.to_openapi_encoding()
        if len(encoding) > 0:
            res["multipart/form-data"]["schema"]["encoding"] = encoding
        return res

    def from_params(self, service, params):
        for key, part in self._parts.items():
            param = None
            if isinstance(part, BinaryData):
                param = part.from_params(service, params[key])
            else:
                # If the part is not Binary, it should be JSON
                try:
                    json_param = json.loads(
                        params[key]
                    )  # multipart ony sends its parts as string
                except json.JSONDecodeError as error:
                    raise ValidationError(
                        service.env._(f"{key}'s JSON content is malformed: {error}")
                    ) from error
                param = part.from_params(service, json_param)
            params[key] = param
        return params

    def to_openapi_query_parameters(self, service, spec):
        raise NotImplementedError(
            "MultipartFormData are not (?yet?) supported as query paramters"
        )

    def to_openapi_requestbody(self, service, spec):
        return {"content": self.to_json_schema(service, spec, "input")}

    def to_openapi_responses(self, service, spec):
        return {"200": {"content": self.to_json_schema(service, spec, "output")}}

    def to_response(self, service, result):
        raise NotImplementedError()
