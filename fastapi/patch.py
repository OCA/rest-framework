# Copyright 2026 ForgeFlow S.L. (https://www.forgeflow.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from urllib.parse import parse_qs, urlparse

import odoo.http.router as http_router
from odoo.http.router import db_filter

_original_set_session_and_dbname = http_router._set_session_and_dbname


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


http_router._set_session_and_dbname = _patched_set_session_and_dbname
