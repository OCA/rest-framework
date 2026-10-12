# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from urllib.parse import parse_qs, urlparse

try:
    import odoo.http.router as http_router
    from odoo.http.requestlib import Request
    from odoo.http.router import db_filter
except ImportError:
    http_router = None
    from odoo.http import Request, db_filter

_original_set_session_and_dbname = (
    getattr(http_router, "_set_session_and_dbname", None) if http_router else None
)
_original_get_session_and_dbname = getattr(Request, "_get_session_and_dbname", None)


def _patched_get_session_and_dbname(self):
    session, dbname = _original_get_session_and_dbname(self)
    if not dbname:
        # Try to get the database from request "db" param.
        # This is useful for multi-database environments.
        db = self.httprequest.args.get("db", "").strip()
        if not db:
            # For browser sub-requests (e.g. openapi.json or static assets fetched
            # by Swagger UI / ReDoc), the browser sets a Referer header pointing
            # to the docs page which may carry the "db" query parameter.
            referer = self.httprequest.headers.get("Referer", "")
            if referer:
                parsed = urlparse(referer)
                db = parse_qs(parsed.query).get("db", [""])[0].strip()
        if db and db_filter([db]):
            dbname = db
            session.db = dbname
    return session, dbname


def _patched_set_session_and_dbname(request):
    _original_set_session_and_dbname(request)
    if not getattr(request, "db", None):
        db = request.httprequest.args.get("db", "").strip()
        if not db:
            referer = request.httprequest.headers.get("Referer", "")
            if referer:
                parsed = urlparse(referer)
                db = parse_qs(parsed.query).get("db", [""])[0].strip()
        host = request.httprequest.environ.get("HTTP_HOST", "")
        if db and db_filter([db], host=host):
            request.db = db
            if hasattr(request, "session") and request.session:
                request.session.db = db


if _original_set_session_and_dbname is not None:
    http_router._set_session_and_dbname = _patched_set_session_and_dbname
elif _original_get_session_and_dbname is not None:
    Request._get_session_and_dbname = _patched_get_session_and_dbname
