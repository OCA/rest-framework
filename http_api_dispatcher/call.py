# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import dataclasses
from functools import cached_property
from typing import Any

from .parsers import read_body, read_query

# Transport data: the CSRF token is never a param of the endpoint
CSRF_TOKEN_PARAM = "csrf_token"


@dataclasses.dataclass
class ApiCall:
    """State of one request going through the `http_api` pipeline.

    Hooks and params receive the call instead of loose arguments,
    so that new attributes can be added without breaking signatures.

    :param request: the current `odoo.http.Request`
    :param endpoint: the matched endpoint
    :param args: arguments extracted from the URL (eg: `<int:id>`)
    The query string and the body are parsed on first access.
    The pipeline reads `params` to call the endpoint, so routes parse both today.

    :param result: result of the endpoint (validated after output validation)
    :param extra: free storage for hooks and plugins
    """

    request: Any
    endpoint: Any
    args: dict
    result: Any = None
    extra: dict = dataclasses.field(default_factory=dict)
    _params: Any = dataclasses.field(default=None, init=False, repr=False)

    @cached_property
    def query(self):
        """Query string params, parsed on first access."""
        return read_query(self.httprequest, self.routing)

    @cached_property
    def body(self):
        """Body params, parsed on first access."""
        return read_body(self.httprequest, self.routing)

    @property
    def params(self):
        """Params passed to the endpoint: query, then body, then URL args.

        Built on first access (raw params before input validation,
        secure params after). The same dict is returned on each access.
        """
        if self._params is None:
            params = {**self.query, **self.body, **self.args}
            params.pop(CSRF_TOKEN_PARAM, None)
            self.params = params
        return self._params

    @params.setter
    def params(self, value):
        self._params = value
        # Keep the request in sync: error logs read it
        self.request.params = value

    @property
    def env(self):
        # Always the current env: hooks might update it (eg: context)
        """Current env: hooks might have changed it (eg: context)."""
        return self.request.env

    @property
    def routing(self):
        """Routing of the endpoint: drives the behavior of the pipeline."""
        return self.endpoint.routing

    @property
    def httprequest(self):
        """Shortcut to the werkzeug request."""
        return self.request.httprequest
