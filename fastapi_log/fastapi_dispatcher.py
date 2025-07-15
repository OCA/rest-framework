# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import registry, tools
from odoo.http import _dispatchers

from odoo.addons.fastapi.fastapi_dispatcher import (
    FastApiDispatcher as BaseFastApiDispatcher,
)

_logger = logging.getLogger(__name__)


# Inherit from last registered fastapi dispatcher
# This handles multiple overload of dispatchers
class FastApiDispatcher(_dispatchers.get("fastapi", BaseFastApiDispatcher)):
    routing_type = "fastapi"

    def dispatch(self, endpoint, args):
        self.request.params = {}
        environ = self._get_environ()
        root_path = "/" + environ["PATH_INFO"].split("/")[1]
        fastapi_endpoint = (
            self.request.env["fastapi.endpoint"]
            .sudo()
            .search([("root_path", "=", root_path)])
        )
        if fastapi_endpoint.log_requests:
            log = None
            try:
                if tools.config["test_enable"]:
                    cr = getattr(
                        self.request.env.registry, "test_log_cr", self.request.env.cr
                    )
                else:
                    # Create an independent cursor
                    cr = registry(self.request.env.cr.dbname).cursor()

                env = self.request.env(cr=cr, su=True)
                try:
                    # cf fastapi _get_environ
                    request = self.request.httprequest._HTTPRequest__wrapped
                except AttributeError:
                    request = self.request.httprequest

                log = env["fastapi.log"].log_request(
                    request, environ, fastapi_endpoint.id
                )
            except Exception as e:
                _logger.warning("Failed to log request", exc_info=e)

            try:
                response = super().dispatch(endpoint, args)
            except Exception as e:
                try:
                    log and log.log_exception(e)
                except Exception as e:
                    _logger.warning("Failed to log exception", exc_info=e)
                raise e
            else:
                try:
                    log and log.log_response(response)
                except Exception as e:
                    _logger.warning("Failed to log response", exc_info=e)
            finally:
                if not tools.config["test_enable"]:
                    try:
                        cr.commit()  # pylint: disable=E8102
                    finally:
                        cr.close()
            return response

        else:
            return super().dispatch(endpoint, args)
