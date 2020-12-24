# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


import logging

from werkzeug.exceptions import NotFound

from odoo.http import request

from odoo.addons.component.core import AbstractComponent

from ..apispec.base_rest_service_apispec import BaseRestServiceAPISpec

_logger = logging.getLogger(__name__)


def to_int(val):
    # The javascript VM ducktape only use float and so pass float
    # to the api, the werkzeug request interpret params as unicode
    # so we have to convert params from string to float to int
    if isinstance(val, int):
        return val
    if val:
        return int(float(val))
    return None


def to_bool(val):
    return val in ("true", "True", "1", True)


def skip_secure_params(func):
    """
    Used to decorate methods
    :param func:
    :return:
    """
    func.skip_secure_params = True
    return func


def skip_secure_response(func):
    """
    Used to decorate methods
    :param func:
    :return:
    """
    func.skip_secure_response = True
    return func


class BaseRestService(AbstractComponent):
    _name = "base.rest.service"

    _description = None  # description included into the openapi doc
    _is_rest_service_component = True  # marker to retrieve REST components

    def _prepare_extra_log(self, func, params, secure_params, res):
        httprequest = request.httprequest
        headers = dict(httprequest.headers)
        return {
            "application": "Rest Service",
            "request_url": httprequest.url,
            "request_method": httprequest.method,
            "params": params,
            "headers": headers,
            "secure_params": secure_params,
            "res": res,
            "status": 200,
        }

    def _log_call(self, func, params, secure_params, res):
        """If you want to enjoy the advanced log install the module
        logging_json"""
        if request:
            httprequest = request.httprequest
            extra = self._prepare_extra_log(func, params, secure_params, res)
            args = [httprequest.url, httprequest.method]
            message = "REST call url %s method %s"
            _logger.debug(message, *args, extra=extra)

    def _prepare_input_params(self, method, params):
        """
        Internal method used to process the input_param parameter. The
        result will be used to call the final method. The processing is
        delegated to the `resapi.RestMethodParam` instance specified by the
        restapi.method` decorator on the method.
        :param method:
        :param params:
        :return:
        """
        method_name = method.__name__
        if hasattr(method, "skip_secure_params"):
            return params
        routing = getattr(method, "routing", None)
        if not routing:
            _logger.warning(
                "Method %s is not a public method of service %s",
                method_name,
                self._name,
            )
            raise NotFound()
        input_param = routing["input_param"]
        if input_param:
            return input_param.from_params(self, params)
        return {}

    def _prepare_response(self, method, result):
        """
        Internal method used to process the result of the method called by the
        controller. The result of this process is returned to the controller

        The processing is delegated to the `resapi.RestMethodParam` instance
        specified by the `restapi.method` decorator on the method.
        :param method: method
        :param response:
        :return: dict/json or `http.Response`
        """
        method_name = method
        if callable(method):
            method_name = method.__name__
        if hasattr(method, "skip_secure_response"):
            return result
        routing = getattr(method, "routing", None)
        output_param = routing["output_param"]
        if not output_param:
            _logger.warning(
                "DEPRECATED: You must define an output schema for method %s "
                "in service %s",
                method_name,
                self._name,
            )
            return result
        return output_param.to_response(self, result)

    def dispatch(self, method_name, *args, params=None):
        """
        This method dispatch the call to the final method.
        Before the call parameters are processed by the
        `restapi.RestMethodParam` object specified as input_param object.
        The result of the method is therefore given to the
        `restapi.RestMethodParam` object specified as output_param to build
        the final response returned by the service
        :param method_name:
        :param *args: query path paramters args
        :param params: A dictionary with the parameters of the method. Once
                       secured and sanitized, these parameters will be passed
                       to the method as keyword args.
        :return:
        """
        method = getattr(self, method_name, object())
        params = params or {}
        secure_params = self._prepare_input_params(method, params)
        if isinstance(secure_params, dict):
            # for backward compatibility methods expecting json params
            # are declared as m(self, p1=None, p2=None) or m(self, **params)
            res = method(*args, **secure_params)
        else:
            res = method(*args, secure_params)
        self._log_call(method, params, secure_params, res)
        return self._prepare_response(method, res)

    def _validator_delete(self):
        """
        Default validator for delete method.
        By default delete should never be called with parameters.
        """
        return {}

    def _validator_get(self):
        """
        Default validator for get method.
        By default get should not be called with parameters.
        """
        return {}

    def to_openapi(self):
        """
        Return the description of this REST service as an OpenAPI json document
        :return: json document
        """
        return BaseRestServiceAPISpec(self).to_dict()

    def _get_openapi_default_parameters(self):
        return []

    def _get_openapi_default_responses(self):
        return {
            "400": {"description": "One of the given parameter is not valid"},
            "401": {
                "description": "The user is not authorized. Authentication "
                "is required"
            },
            "404": {"description": "Requested resource not found"},
            "403": {
                "description": "You don't have the permission to access the "
                "requested resource."
            },
        }
