# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging
from collections import defaultdict

from werkzeug.exceptions import BadRequest

from odoo.http import (
    CSRF_FREE_METHODS,
    MISSING_CSRF_WARNING,
    Dispatcher,
)

from .call import CSRF_TOKEN_PARAM, ApiCall
from .errors import ErrorMapper

_logger = logging.getLogger(__name__)

CSRF_TOKEN_HEADER = "X-CSRF-Token"


class HttpApiDispatcher(Dispatcher):
    """Dispatcher for routes of type `http_api`.

    Heavily inspired by `RestApiDispatcher` in `base_rest.http`
    (OCA/rest-framework): body parsing, CSRF check
    and language detection follow the same rules.

    This class is process-global (like any Odoo dispatcher):
    keep it thin and stateless.
    Behaviors depending on installed modules
    are delegated to `ir.http._http_api_*` hooks,
    behaviors specific to a route are driven by its routing keys.
    """

    routing_type = "http_api"

    @classmethod
    def is_compatible_with(cls, request):
        """Accept any content type: parsers decide how to read the body."""
        return True

    def pre_dispatch(self, rule, args):
        """Set the language before the endpoint is called.

        Params are not parsed here: see `ApiCall`.
        Keep the routing: `handle_error` needs it to apply the route error map.
        """
        res = super().pre_dispatch(rule, args)
        self.routing = rule.endpoint.routing
        self._set_lang_from_headers()
        return res

    def dispatch(self, endpoint, args):
        """Check CSRF and run the `ir.http` pipeline.

        The pipeline lives in `ir.http` so that it can be extended per database.
        """
        call = ApiCall(request=self.request, endpoint=endpoint, args=args)
        self._check_csrf(endpoint, call)
        return self.request.registry["ir.http"]._http_api_run(call)

    def handle_error(self, exc):
        """Return a JSON error response, honoring the error map of the route."""
        routing = getattr(self, "routing", None)
        return ErrorMapper.for_routing(routing, request=self.request).to_response(exc)

    def _check_csrf(self, endpoint, call):
        """Validate the CSRF token as Odoo does for `http` routes.

        The token is read from the `X-CSRF-Token` header first:
        the query and the body are parsed only when the header is missing.
        Token based APIs should disable the check via `csrf=False`.
        """
        if self.request.httprequest.method in CSRF_FREE_METHODS:
            return
        if not endpoint.routing.get("csrf", True):
            return
        token = self.request.httprequest.headers.get(CSRF_TOKEN_HEADER)
        if token is None:
            token = call.body.get(CSRF_TOKEN_PARAM, call.query.get(CSRF_TOKEN_PARAM))
        if not self.request.validate_csrf(token):
            if token is not None:
                _logger.warning(
                    "CSRF validation failed on path '%s'",
                    self.request.httprequest.path,
                )
            else:
                _logger.warning(MISSING_CSRF_WARNING, self.request.httprequest.path)
            raise BadRequest("Session expired (invalid CSRF token)")

    def _set_lang_from_headers(self):
        """Set the lang in context from `Accept-Language` header.

        The first installed language matching the header,
        by priority, is used: exact locale match first (eg: `fr_BE`)
        then language match (eg: `fr` -> first installed `fr_*`).
        """
        accepted = self.request.httprequest.accept_languages
        if not accepted:
            return
        installed = set()
        by_lang = defaultdict(list)
        for code, __ in self.request.env["res.lang"].get_installed():
            installed.add(code)
            by_lang[code.split("_")[0]].append(code)
        for value in accepted.values():
            locale = value.replace("-", "_")
            lang = locale if locale in installed else None
            if not lang and by_lang.get(locale.split("_")[0]):
                lang = by_lang[locale.split("_")[0]][0]
            if lang:
                self.request.update_context(lang=lang)
                return
