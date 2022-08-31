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
            parameters = self._generate_pamareters(routing, method, params)
            if parameters:
                params["parameters"] = parameters
            responses = self._generate_responses(routing, method, params)
            if responses:
                params["responses"] = responses

    def _generate_pamareters(self, routing, method, params):
        parameters = params.get("parameters", [])
        # add default paramters provided by the sevice
        parameters.extend(self._default_parameters)
        input_param = routing.get("input_param")
        if input_param and isinstance(input_param, RestMethodParam):
            if method == "get":
                # get quey params from RequestMethodParam object
                parameters.extend(
                    input_param.to_openapi_query_parameters(self._service, self.spec)
                )
            else:
                # get requestBody from RequestMethodParam object
                request_body = params.get("requestBody", {})
                request_body.update(
                    input_param.to_openapi_requestbody(self._service, self.spec)
                )
                params["requestBody"] = request_body
            # sort paramters to ease comparison into unittests
            parameters.sort(key=lambda a: a["name"])
        return parameters

    def _generate_responses(self, routing, method, params):
        responses = params.get("responses", {})
        # add default responses provided by the service
        responses.update(self._default_responses.copy())
        output_param = routing.get("output_param")
        if output_param and isinstance(output_param, RestMethodParam):
            responses = params.get("responses", {})
            # get response from RequestMethodParam object
            responses.update(self._default_responses.copy())
            responses.update(
                output_param.to_openapi_responses(self._service, self.spec)
            )
        return responses
