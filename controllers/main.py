# -*- coding: utf-8 -*-
# Copyright 2016 Akretion (http://www.akretion.com)
# Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from contextlib import contextmanager

from odoo.addons.component.core import WorkContext
from odoo.http import Controller, Response, request
from werkzeug.exceptions import BadRequest

_logger = logging.getLogger(__name__)


class _PseudoCollection(object):
    def __init__(self, name, env):
        self._name = name
        self.env = env


class RestController(Controller):

    def _get_component_context(self):
        """
        This method can be inherited to add parameter into the component
        context
        :return: dict of key value.
        """
        return {'request': request}

    def make_response(self, data):
        if isinstance(data, Response):
            # The response has been build by the called method...
            return data
        # By default return result as json
        return request.make_json_response(data)

    @contextmanager
    def work_on_component(self):
        """
        Return the component that implements the methods of the requested
        service.
        :param service_name:
        :return: an instance of invader.service component
        """
        collection = _PseudoCollection(request.collection_name, request.env)
        params = self._get_component_context()
        yield WorkContext(model_name='rest.service.registration',
                          collection=collection, **params)

    @contextmanager
    def service_component(self, service_name):
        """
        Return the component that implements the methods of the requested
        service.
        :param service_name:
        :return: an instance of invader.service component
        """
        with self.work_on_component() as work:
            service = work.component(usage=service_name)
            yield service

    def _validate_method_name(self, method_name):
        if method_name.startswith('_'):
            _logger.error("Invader service called with an unallowed method "
                          "name: %s.\n Method can't start with '_'",
                          method_name)
            raise BadRequest()
        return True

    def _process_method(self, service_name, method_name, _id=None,
                        params=None):
        self._validate_method_name(method_name)
        with self.service_component(service_name) as service:
            res = service.dispatch(method_name, _id, params)
            return self.make_response(res)
