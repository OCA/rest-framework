# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from apispec import BasePlugin

from odoo.addons.base_rest.tools import ROUTING_DECORATOR_ATTR


class RestMethodSecurityPlugin(BasePlugin):
    def __init__(self, service):
        super().__init__()
        self._service = service

    # pylint: disable=W8110
    def init_spec(self, spec):
        super().init_spec(spec)
        self.spec = spec
        self.openapi_version = spec.openapi_version
        jwt_scheme = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "name": "jwt",
            "description": "Enter JWT Bearer Token ** only **",
        }
        spec.components.security_scheme("jwt", jwt_scheme)

    def operation_helper(self, path=None, operations=None, **kwargs):
        routing = kwargs.get(ROUTING_DECORATOR_ATTR)
        if not routing:
            super().operation_helper(path, operations, **kwargs)
        if not operations:
            return
        default_auth = self.spec._params.get("default_auth")
        auth = routing.get("auth", default_auth)
        if (auth and auth.startswith("jwt")) or (
            auth == "public_or_default"
            and default_auth
            and default_auth.startswith("jwt")
        ):
            for _method, params in operations.items():
                security = params.setdefault("security", [])
                security.append({"jwt": []})
