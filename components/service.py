# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# Copyright 2017 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


import logging

from odoo.addons.component.core import Component
from odoo.exceptions import UserError
from odoo.http import request
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


try:
    from cerberus import Validator
except ImportError:
    _logger.debug('Can not import cerberus')


def to_int(val):
    # The javascript VM ducktape only use float and so pass float
    # to the api, the werkzeug request interpret params as unicode
    # so we have to convert params from string to float to int
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


class BaseRestService(Component):
    _name = 'base.rest.service'

    def _prepare_extra_log(self, func, params, secure_params, res):
        httprequest = request.httprequest
        headers = dict(httprequest.headers)
        headers.pop('Api-Key')
        return {
            'application': 'Rest Service',
            'invader_url': httprequest.url,
            'invader_method': httprequest.method,
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
            message = 'Invader call url %s method %s'
            _logger.debug(message, *args, extra=extra)

    def _get_schema_for_method(self, method_name):
        validator_method = '_validator_%s' % method_name
        if not hasattr(self, validator_method):
            raise NotImplementedError(validator_method)
        return getattr(self, validator_method)()

    def _validate_list(self, schema, params):
        for field, vals in schema.items():
            if vals.get('type') == 'list' and params.get(field):
                v = Validator(vals['schema'], purge_unknown=True)
                parsed = []
                for elem in params[field]:
                    if not v.validate(elem):
                        _logger.error("BadRequest %s", v.errors)
                        raise UserError(_('Invalid Form'))
                    parsed.append(v.document)
                params[field] = parsed
        return params

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
            # TODO we should fix cerberus issue
            # https://github.com/pyeve/cerberus/issues/325
            return self._validate_list(schema, v.document)
        _logger.error("BadRequest %s", v.errors)
        raise UserError(_('Invalid Form'))

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
            raise NotImplementedError('Method %s not found in service %s' %
                                      method_name, self._name)
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
