# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Default parsers for request bodies and query strings.

Body parsers are selected by mimetype.
Each parser receives the werkzeug request and returns a dict.
Routes can override them via `body_parsers` and `query_parser` routing keys.
"""

import json
import logging

from werkzeug.exceptions import BadRequest

_logger = logging.getLogger(__name__)


def parse_query(httprequest):
    """Flat dict of query string params (last value wins)."""
    return httprequest.args.to_dict(flat=True)


def parse_json(httprequest):
    """Parse a JSON object from the body.

    Only objects are accepted as their keys become the params of the endpoint.
    """
    charset = httprequest.mimetype_params.get("charset", "utf-8")
    data = httprequest.get_data().decode(charset)
    if not data:
        return {}
    try:
        value = json.loads(data)
    except ValueError as err:
        msg = f"Invalid JSON data: {err}"
        _logger.info("%s: %s", httprequest.path, msg)
        raise BadRequest(msg) from err
    if not isinstance(value, dict):
        raise BadRequest("Invalid JSON data: an object is expected")
    return value


def parse_form(httprequest):
    """Form fields and files (flat)."""
    params = httprequest.form.to_dict(flat=True)
    params.update(httprequest.files.to_dict(flat=True))
    return params


DEFAULT_BODY_PARSERS = {
    "application/json": parse_json,
    "multipart/form-data": parse_form,
    "application/x-www-form-urlencoded": parse_form,
}


def read_query(httprequest, routing):
    """Query string params, with the `query_parser` of the route if any."""
    parser = routing.get("query_parser") or parse_query
    return parser(httprequest)


def read_body(httprequest, routing):
    """Body params, with the `body_parsers` of the route (by mimetype) if any."""
    parsers = dict(DEFAULT_BODY_PARSERS, **(routing.get("body_parsers") or {}))
    parser = parsers.get(httprequest.mimetype)
    if not parser:
        return {}
    return parser(httprequest)
