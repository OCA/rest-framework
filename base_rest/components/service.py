# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import inspect
import logging
import textwrap
from collections import OrderedDict

from odoo.addons.component.core import AbstractComponent
from odoo.exceptions import UserError, ValidationError
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

    def _get_input_schema(self, method_name):
        validator_method = '_validator_%s' % method_name
        if not hasattr(self, validator_method):
            return None
        return getattr(self, validator_method)()

    def _get_output_schema(self, method_name):
        validator_method = '_validator_return_%s' % method_name
        if not hasattr(self, validator_method):
            return None
        return getattr(self, validator_method)()

    def _secure_input(self, method, params):
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
        schema = self._get_input_schema(method_name)
        if schema is None:
            raise ValidationError(
                _("No input schema defined for method %s in service %s") %
                (method_name, self._name)
            )
        v = Validator(schema, purge_unknown=True)
        if v.validate(params):
            return v.document
        raise UserError(_('BadRequest %s') % v.errors)

    def _secure_output(self, method, response):
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
        schema = self._get_output_schema(method_name)
        if not schema:
            _logger.warning(
                "DEPRECATED: You must define an output schema for method %s "
                "in service %s", method_name, self._name)
            return response
        v = Validator(schema, purge_unknown=True)
        if v.validate(response):
            return v.document
        raise SystemError(_('Invalid Response %s') % v.errors)

    def dispatch(self, method_name, _id=None, params=None):
        """
        This method dispatch the call to expected public method name.
        Before the call the parameters are secured by a call to
        `secure_input` and the result is also secured by a call to
        `_secure_output`
        :param method_name:
        :param _id:
        :param params: A dictionary with the parameters of the method. Once
                       secured and sanitized, these parameters will be passed
                       to the method as keyword args.
        :return:
        """
        params = params or {}
        if not self._is_public_api_method(method_name):
            _logger.warning(
                'Method %s is not a public method of service %s',
                method_name, self._name)
            raise NotFound()
        func = getattr(self, method_name, None)
        secure_params = self._secure_input(func, params)
        if _id:
            secure_params['_id'] = _id
        res = func(**secure_params)
        self._log_call(func, params, secure_params, res)
        return self._secure_output(func, res)

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
        root = OrderedDict()
        root['openapi'] = '3.0.0'
        root['info'] = self._get_openapi_info()
        root['servers'] = self._get_openapi_servers()
        root['paths'] = self._get_openapi_paths()
        return root

    def _get_openapi_info(self):
        return {
            'title': "%s REST services" % self._usage,
            'description': textwrap.dedent(getattr(self, '_description', ''))
        }

    def _get_openapi_servers(self):
        services_registry = _rest_services_databases.get(
            self.env.cr.dbname, {})
        collection_path = ''
        for path, spec in services_registry.items():
            if spec['collection_name'] == self._collection:
                collection_path = path[1:-1]  # remove '/'
                break
        return [{'url': "%s/%s/%s" % (
            self.env['ir.config_parameter'].get_param('web.base.url'),
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

    def _is_public_api_method(self, method_name):
        """
        Return True if the method is into the public API
        :param method_name:
        :return:
        """
        if method_name.startswith('_'):
            return False
        if not hasattr(self, method_name):
            return False
        if hasattr(BaseRestService, method_name):
            # exclude methods from base class
            return False
        return True

    def _get_openapi_paths(self):
        paths = OrderedDict()
        public_methods = {}
        for name, data in inspect.getmembers(self, inspect.ismethod):
            if not self._is_public_api_method(name):
                continue
            public_methods[name] = data

        for name, method in public_methods.items():
            id_in_path_required = False
            arg_spec = inspect.getargspec(method)
            if '_id' in arg_spec.args:
                id_in_path_required = True
            if '_id' in (arg_spec.keywords or {}):
                id_in_path_required = True
            parameters = self._get_openapi_default_parameters()
            responses = self._get_openapi_default_responses().copy()
            path_info = {
                'summary': textwrap.dedent(method.__doc__ or ''),
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
            input_schema = self._get_input_schema(name)
            output_schema = self._get_output_schema(name)
            json_input_schema = cerberus_to_json(
                input_schema)

            if not output_schema:
                # for backward compatiibility output schema is not required
                # DEPRECATED
                responses['200'] = {
                    'description': "Unknown response type"
                }
            else:
                json_output_schema = cerberus_to_json(
                    output_schema
                )
                responses['200'] = {
                    'content': {
                        'application/json': {
                            'schema': json_output_schema
                        }
                    }
                }

            if name in ('search', 'get'):
                get = {'get': path_info}
                # parameter for http GET are url query parameters
                for prop, spec in json_input_schema['properties'].items():
                    params = {
                        'name': prop,
                        'in': 'query',
                        'required': prop in json_input_schema['required'],
                        'allowEmptyValue': spec.get('nullable', False),
                        'default': spec.get('default'),
                    }
                    if spec.get('schema'):
                        params['schema'] = spec.get('schema')
                    else:
                        params['schema'] = {'type': spec['type']}
                    if spec.get('items'):
                        params['schema']['items'] = spec.get('items')
                    if 'enum' in spec:
                        params['schema']['enum'] = spec['enum']

                    parameters.append(params)

                    if spec['type'] == 'array':
                        # To correctly handle array into the url query string,
                        # the name must ends with []
                        params['name'] = params['name'] + '[]'

                if name == 'get':
                    paths.setdefault('/{id}', {}).update(get)
                    paths['/{id}/get'] = get
                if name == 'search':
                    paths['/'] = get
                    paths['/search'] = get
            elif name == 'delete':
                paths.setdefault('/{id}', {}).update({'delete': path_info})
                paths['/{id}/delete'] = {
                    'post': path_info}
            else:
                # parameter for HTTP Post are given as a json document into the
                # requestBody
                path_info['requestBody'] = {
                    'content': {
                        'application/json': {
                            'schema': json_input_schema
                        }
                    }
                }
                path = '/' + name
                if id_in_path_required:
                    path = '/{id}/' + name
                paths[path] = {'post': path_info}
                if name == 'update':
                    paths.setdefault('/{id}', {}).update({'put': path_info})
            # sort paramters to ease comparison into unittests
            parameters.sort(key=lambda a: a['name'])
        return paths
