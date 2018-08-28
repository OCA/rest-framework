# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import inspect
import logging
from collections import OrderedDict

from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.translate import _
from werkzeug.exceptions import NotFound

from ..core import _rest_services_databases
from ..tools import cerberus_to_json

_logger = logging.getLogger(__name__)

try:
    from cerberus import Validator
except ImportError:
    _logger.debug('Can not import cerberus')


def to_int(val):
    # The javascript VM ducktape only use float and so pass float
    # to the api, the werkzeug request interpret params as unicode
    # so we have to convert params from string to float to int
    if isinstance(val, (int, long)):
        return val
    if val:
        return int(float(val))
    else:
        return None


def to_bool(val):
    return val in ('true', 'True', '1', True)


def skip_secure_params(func):
    """
    Used to decorate methods
    :param func:
    :return:
    """
    func.skip_secure_params = True


def skip_secure_response(func):
    """
    Used to decorate methods
    :param func:
    :return:
    """
    func.skip_secure_response = True


class BaseRestService(AbstractComponent):
    _name = 'base.rest.service'

    _desciption = None  # sdescription included into the openapi doc
    _is_rest_service_component = True  # marker to retrieve REST components

    def _prepare_extra_log(self, func, params, secure_params, res):
        httprequest = request.httprequest
        headers = dict(httprequest.headers)
        return {
            'application': 'Rest Service',
            'request_url': httprequest.url,
            'request_method': httprequest.method,
            'params': params,
            'headers': headers,
            'secure_params': secure_params,
            'res': res,
            'status': 200,
        }

    def _log_call(self, func, params, secure_params, res):
        """If you want to enjoy the advanced log install the module
        logging_json"""
        if request:
            httprequest = request.httprequest
            extra = self._prepare_extra_log(func, params, secure_params, res)
            args = [httprequest.url, httprequest.method]
            message = 'REST call url %s method %s'
            _logger.debug(message, *args, extra=extra)

    def _get_validator_method(self, method_name):
        validator_method = '_validator_%s' % method_name
        return getattr(self, validator_method, None)

    def _get_schema_for_method(self, method_name):
        validator_method = self._get_validator_method(method_name)
        if not validator_method:
            raise NotImplementedError(validator_method)
        return validator_method()

    def _get_schema_output_for_method(self, method_name):
        validator_method = '_validator_return_%s' % method_name
        if not hasattr(self, validator_method):
            raise NotImplementedError(validator_method)
        return getattr(self, validator_method)()

    def _secure_params(self, method, params):
        """
        This internal method is used to validate and sanitize the parameters
        expected by the given method.  These parameters are validated and
        sanitized according to a schema provided by a method  following the
        naming convention: '_validator_{method_name}'. If the method is
        decorated with `@skip_secure_params` the check and sanitize of the
        parameters are skipped.
        :param method:
        :param params:
        :return:
        """
        method_name = method.__name__
        if hasattr(method, 'skip_secure_params'):
            return params
        schema = self._get_schema_for_method(method_name)
        v = Validator(schema, purge_unknown=True)
        if v.validate(params):
            return v.document
        _logger.error("BadRequest %s", v.errors)
        raise UserError(_('Invalid Form'))

    def _secure_response(self, method, response):
        """
        Internal method used to validate the output of the given method.
        This response is validated according to a schema defined for the
        method, with the convention '_validator_return_{method_name}'.
        If the method is decorated with `@skip_secure_response` checks of
        the response are skipped.
        :param method: str or function
        :param response: dict/json
        :return: dict/json
        """
        method_name = method
        if callable(method):
            method_name = method.__name__
        if hasattr(method, 'skip_secure_response'):
            return response
        schema = self._get_schema_output_for_method(method_name)
        v = Validator(schema, purge_unknown=True)
        if v.validate(response):
            return v.document
        _logger.error("Invalid response %s", v.errors)
        raise UserError(_('Invalid Response'))

    def secure_response(self, method, response):
        """
        Check the response for the given method
        :param method: str
        :param response: dict
        :return: dict
        """
        return self._secure_response(method, response)

    def dispatch(self, method_name, _id=None, params=None):
        """
        This method dispatch the call to expected method name. Before the call
        the parameters are secured by a call to `secure_params`.
        :param method_name:
        :param _id:
        :param params: A dictionary with the parameters of the method. Once
                       secured and sanitized, these parameters will be passed
                       to the method as keyword args.
        :return:
        """
        params = params or {}
        func = getattr(self, method_name, None)
        if not func:
            _logger.warning('Method %s not found in service %s',
                            method_name, self._name)
            raise NotFound()

        secure_params = self._secure_params(func, params)
        if _id:
            secure_params['_id'] = _id
        res = func(**secure_params)
        self._log_call(func, params, secure_params, res)
        return res

    def _validator_delete(self):
        """
        Default validator for delete method.
        By default delete should never be called with parameters.
        """
        return {}

    def to_openapi(self):
        """
        Return the description of this REST service as an OpenAPI json document
        :return: json document
        """
        root = OrderedDict()
        root['openapi'] = '3.0.0'
        root['info'] = self._get_openapi_info()
        root['servers'] = self._get_openapi_servers()
        root['paths'] = self._get_openapi_paths()
        return root

    def _get_openapi_info(self):
        return {
            'title': "%s REST services" % self._usage,
            'description': getattr(self, '_description', '')
        }

    def _get_openapi_servers(self):
        env = request.env
        services_registry = _rest_services_databases.get(
            self.env.cr.dbname, {})
        collection_path = ''
        for path, spec in services_registry.items():
            if spec['collection_name'] == self._collection:
                collection_path = path[1:-1]  # remove '/'
                break
        return [{'url': "%s/%s/%s" % (
            env['ir.config_parameter'].get_param('web.base.url'),
            collection_path,
            self._usage,
        )}]

    def _get_openapi_default_parameters(self):
        return []

    def _get_openapi_default_responses(self):
        return {
            '400': {
                'description': "One of the given parameter is not valid",
            },
            '401': {
                'description': "The user is not authorized. Authentication "
                               "is required",
            },
            '404': {
                'description': "Requested resource not found",
            },
            '403': {
                'description': "You don\'t have the permission to access the "
                               "requested resource.",
            }
        }

    def _get_openapi_paths(self):
        paths = OrderedDict()
        public_methods = {}
        for name, data in inspect.getmembers(self, inspect.ismethod):
            if name.startswith('_'):
                continue
            public_methods[name] = data

        for name, method in public_methods.items():
            if not self._get_validator_method(name):
                # we only keep methods with validators
                continue
            id_in_path_required = False
            arg_spec = inspect.getargspec(method)
            if '_id' in arg_spec.args:
                id_in_path_required = True
            if '_id' in (arg_spec.keywords or {}):
                id_in_path_required = True
            parameters = self._get_openapi_default_parameters()
            responses = self._get_openapi_default_responses().copy()
            path_info = {
                'summary': method.__doc__,
                'parameters': parameters,
                'responses': responses,
            }
            if id_in_path_required:
                parameters.append({
                    "name": "id",
                    "in": "path",
                    "description": "Item id",
                    "required": True,
                    "schema": {
                        "type": "integer",
                    }
                })
            request_schema = self._get_schema_for_method(name)
            json_request_schema = cerberus_to_json(
                request_schema)
            json_response_schema = cerberus_to_json(
                self._get_schema_output_for_method(name)
            )
            responses['200'] = {
                'content': {
                    'application/json': {
                        'schema': json_response_schema
                    }
                }
            }
            if name in ('search', 'get'):
                get = {'get': path_info}
                # parameter for http GET are url query parameters
                for prop, spec in json_request_schema['properties'].items():
                    params = {
                        'name': prop,
                        'in': 'query',
                        'required': prop in json_request_schema['required'],
                        'allowEmptyValue': spec.get('nullable', False),
                        'default': spec.get('default'),
                    }
                    if spec.get('schema'):
                        params['schema'] = spec.get('schema')
                    else:
                        params['schema'] = {'type': spec['type']}
                    if spec.get('items'):
                        params['schema']['items'] = spec.get('items')
                    parameters.append(params)

                    if spec['type'] == 'array':
                        # To correctly handle array into the url query string,
                        # the name must ends with []
                        params['name'] = params['name'] + '[]'

                if name == 'get':
                    paths['/{id}'] = get
                    paths['/{id}/get'] = get
                if name == 'search':
                    paths['/'] = get
                    paths['/search'] = get
            elif name == 'delete':
                paths['/{id}'] = {'delete': path_info}
                paths['/{id}/delete'] = {
                    'post': path_info}
            else:
                # parameter for HTTP Post are given as a json document into the
                # requestBody
                path_info['requestBody'] = {
                    'content': {
                        'application/json': {
                            'schema': json_request_schema
                        }
                    }
                }
                path = '/' + name
                if id_in_path_required:
                    path = '/{id}/' + name
                paths[path] = {'post': path_info}
        return paths
