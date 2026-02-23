# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from apispec import BasePlugin

from ..tools import ROUTING_DECORATOR_ATTR


class RestMethodSecurityPlugin(BasePlugin):
    """
    APISpec plugin to generate path security from a services method
    """

    def __init__(self, service, user_auths=("user",)):
        super().__init__()
        self._service = service
        self._supported_user_auths = user_auths

    # pylint: disable=W8110
    def init_spec(self, spec):
        super().init_spec(spec)
        self.spec = spec
        self.openapi_version = spec.openapi_version
        user_scheme = {"type": "apiKey", "in": "cookie", "name": "session_id"}
        spec.components.security_scheme("user", user_scheme)

    def operation_helper(self, path=None, operations=None, **kwargs):
        routing = kwargs.get(ROUTING_DECORATOR_ATTR)
        if not routing:
            super().operation_helper(path, operations, **kwargs)
        if not operations:
            return
        auth = routing.get("auth", self.spec._params.get("default_auth"))
        if auth in self._supported_user_auths:
            for _method, params in operations.items():
                security = params.setdefault("security", [])
                security.append({"user": []})
