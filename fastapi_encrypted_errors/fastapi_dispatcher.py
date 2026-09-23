# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.http import _dispatchers

from odoo.addons.fastapi.error_handlers import convert_exception_to_status_body
from odoo.addons.fastapi.fastapi_dispatcher import (
    FastApiDispatcher as BaseFastApiDispatcher,
)


# Inherit from last registered fastapi dispatcher
# This handles multiple overload of dispatchers
class FastApiDispatcher(_dispatchers.get("fastapi", BaseFastApiDispatcher)):
    routing_type = "fastapi"

    def handle_error(self, exc):
        environ = self._get_environ()
        root_path = "/" + environ["PATH_INFO"].split("/")[1]
        fastapi_endpoint = (
            self.request.env["fastapi.endpoint"]
            .sudo()
            .search([("root_path", "=", root_path)])
        )
        if fastapi_endpoint.encrypt_errors:
            headers = getattr(exc, "headers", None)
            status_code, body = convert_exception_to_status_body(exc)
            if body:
                body["ref"] = fastapi_endpoint._encrypt_error(exc)
            return self.request.make_json_response(
                body, status=status_code, headers=headers
            )

        return super().handle_error(exc)
