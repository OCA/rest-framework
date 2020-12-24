# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import functools

from cerberus import Validator

from odoo import _
from odoo.exceptions import UserError

from .tools import cerberus_to_json


def method(
    routes, input_param=None, output_param=None, auth=None, cors=None, csrf=False
):
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
      :param auth: The type of authentication method
      :param cors: The Access-Control-Allow-Origin cors directive value.
      :param bool csrf: Whether CSRF protection should be enabled for the route.
                        Defaults to ``False``

    """

    def decorator(f):
        _routes = []
        for paths, http_method in routes:
            if not isinstance(paths, list):
                paths = [paths]
            _routes.append(([p for p in paths], http_method))
        routing = {
            "csrf": csrf,
            "auth": auth,
            "cors": cors,
            "routes": _routes,
            "input_param": input_param,
            "output_param": output_param,
        }

        @functools.wraps(f)
        def response_wrap(*args, **kw):
            response = f(*args, **kw)
            return response

        response_wrap.routing = routing
        response_wrap.original_func = f
        return response_wrap

    return decorator


class RestMethodParam(object):
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

    def to_response(self, service, result):
        """
        This method is called to prepare the result of the call to the method
        in a format suitable by the controller (http.Response or JSON dict).
        It's responsible for validating and sanitizing the result.
        :param service:
        :param obj:
        :return: http.Response or JSON dict
        """

    def to_openapi_query_parameters(self, service):
        return {}

    def to_openapi_requestbody(self, service):
        return {}

    def to_openapi_responses(self, service):
        return {}


class CerberusValidator(RestMethodParam):
    def __init__(self, schema=None, is_list=False):
        """

        :param schema: can be dict as cerberus schema, an instance of
                       cerberus.Validator or a sting with the method name to
                       call on the service to get the schema or the validator
        :param is_list: Not implemented. Should be set to True if params is a
                        collection so that the object will be de/serialized
                        from/to a list
        """
        self._schema = schema
        self._is_list = is_list

    def from_params(self, service, params):
        validator = self.get_cerberus_validator(service)
        if validator.validate(params):
            return validator.document
        raise UserError(_("BadRequest %s") % validator.errors)

    def to_response(self, service, result):
        validator = self.get_cerberus_validator(service)
        if validator.validate(result):
            return validator.document
        raise SystemError(_("Invalid Response %s") % validator.errors)

    def to_openapi_query_parameters(self, service):
        json_schema = self.to_json_schema(service)
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

    def to_openapi_requestbody(self, service):
        return {
            "content": {"application/json": {"schema": self.to_json_schema(service)}}
        }

    def to_openapi_responses(self, service):
        json_schema = self.to_json_schema(service)
        return {"200": {"content": {"application/json": {"schema": json_schema}}}}

    def get_cerberus_validator(self, service):
        schema = self._schema
        if isinstance(self._schema, str):
            # schema is a method name to call on service to get the schema or
            schema = getattr(service, self._schema)()
        if isinstance(schema, Validator):
            return schema
        if isinstance(schema, dict):
            return Validator(schema, purge_unknown=True)
        raise Exception(_("Unable to get cerberus schema from %s") % self._schema)

    def to_json_schema(self, service):
        schema = self.get_cerberus_validator(service).schema
        return cerberus_to_json(schema)
