# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from apispec import BasePlugin


class RestMethodSecurityPlugin(BasePlugin):
    """
    APISpec plugin to generate path security from a services method
    """

    def __init__(self, service):
        super(RestMethodSecurityPlugin, self).__init__()
        self._service = service

    def init_spec(self, spec):
        super(RestMethodSecurityPlugin, self).init_spec(spec)
        self.spec = spec
        self.openapi_version = spec.openapi_version
        user_scheme = {"type": "apiKey", "in": "cookie", "name": "session_id"}
        spec.components.security_scheme("user", user_scheme)

    def operation_helper(self, path=None, operations=None, **kwargs):
        routing = kwargs.get("routing")
        if not routing:
            super(RestMethodSecurityPlugin, self).operation_helper(
                path, operations, **kwargs
            )
        if not operations:
            return
        auth = routing.get("auth", self.spec._params.get("default_auth"))
        if auth == "user":
            for _method, params in operations.items():
                security = params.setdefault("security", [])
                security.append({"user": []})
