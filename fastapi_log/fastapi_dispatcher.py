# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from contextlib import contextmanager

from odoo.http import _dispatchers
from odoo.modules.registry import Registry

from odoo.addons.fastapi.fastapi_dispatcher import (
    FastApiDispatcher as BaseFastApiDispatcher,
)

_logger = logging.getLogger(__name__)


# Inherit from last registered fastapi dispatcher
# This handles multiple overload of dispatchers
class FastApiDispatcher(_dispatchers.get("fastapi", BaseFastApiDispatcher)):
    routing_type = "fastapi"

    @contextmanager
    def _create_log_env(self, request_env):
        request_registry = request_env.registry
        if request_registry.in_test_mode():
            # During tests, use the dedicated test's cursor
            cr = request_registry.test_log_cr
        else:
            # Create an independent cursor
            # so the logs are committed despite any endpoint's exceptions
            cr = Registry(request_registry.db_name).cursor()

        try:
            yield request_env(cr=cr, su=True)
        finally:
            # While executing tests,
            # the cursor is already managed in the tests
            if not request_registry.in_test_mode():
                try:
                    cr.commit()  # pylint: disable=invalid-commit
                finally:
                    cr.close()

    def dispatch(self, endpoint, args):
        self.request.params = {}
        environ = self._get_environ()
        fastapi_endpoint = (
            self.request.env["fastapi.endpoint"]
            .sudo()
            ._get_endpoint(environ["PATH_INFO"])
        )
        if fastapi_endpoint.log_requests:
            with self._create_log_env(self.request.env) as log_env:
                try:
                    log = log_env["api.log"].log_request(self.request)
                except Exception as e:
                    _logger.warning("Failed to log request", exc_info=e)
                    log = None

                try:
                    response = super().dispatch(endpoint, args)
                except Exception as response_exc:
                    try:
                        log and log.log_exception(response_exc)
                    except Exception as e:
                        _logger.warning("Failed to log exception", exc_info=e)

                    raise response_exc
                else:
                    try:
                        log and log.log_response(response)
                    except Exception as e:
                        _logger.warning("Failed to log response", exc_info=e)

                return response
        else:
            return super().dispatch(endpoint, args)
