# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from apispec import BasePlugin

from ..restapi import RestMethodParam


class RestMethodParamPlugin(BasePlugin):
    """
    APISpec plugin to generate path from a services method
    """

    def __init__(self, service):
        super(RestMethodParamPlugin, self).__init__()
        self._service = service
        self._default_parameters = service._get_openapi_default_parameters()
        self._default_responses = service._get_openapi_default_responses()

    def init_spec(self, spec):
        super(RestMethodParamPlugin, self).init_spec(spec)
        self.spec = spec
        self.openapi_version = spec.openapi_version

    def operation_helper(self, path=None, operations=None, **kwargs):
        routing = kwargs.get("routing")
        if not routing:
            super(RestMethodParamPlugin, self).operation_helper(
                path, operations, **kwargs
            )
        if not operations:
            return
        for method, params in operations.items():
            input_param = routing.get("input_param")
            output_param = routing.get("output_param")
            if input_param and isinstance(input_param, RestMethodParam):
                parameters = params.get("parameters", [])
                # add default paramters provided by the sevice
                parameters.extend(self._default_parameters)
                if method == "get":
                    # get quey params from RequestMethodParam object
                    parameters.extend(
                        input_param.to_openapi_query_parameters(self._service)
                    )
                    # sort paramters to ease comparison into unittests
                else:
                    # get requestBody from RequestMethodParam object
                    request_body = params.get("requestBody", {})
                    request_body.update(
                        input_param.to_openapi_requestbody(self._service)
                    )
                    params["requestBody"] = request_body
                parameters.sort(key=lambda a: a["name"])
                params["parameters"] = parameters
            if output_param and isinstance(output_param, RestMethodParam):
                responses = params.get("responses", {})
                # get response from RequestMethodParam object
                responses.update(self._default_responses.copy())
                responses.update(output_param.to_openapi_responses(self._service))
                params["responses"] = responses
