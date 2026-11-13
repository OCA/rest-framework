# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import datetime
import decimal

from werkzeug.exceptions import Conflict

from odoo import exceptions, http
from odoo.http import request

from ..errors import ApiValidationError
from ..params import ApiParam


class ConflictError(Exception):
    pass


class NameParam(ApiParam):
    """Require a `name` string, drop anything else."""

    def from_params(self, call):
        name = call.params.get("name")
        if not isinstance(name, str) or not name:
            raise ApiValidationError("BadRequest name", errors={"name": ["required"]})
        return {"name": name.strip()}

    def to_response(self, call, result):
        if "greeting" not in result:
            raise SystemError("Invalid Response")
        return {"greeting": result["greeting"]}

    def to_json_schema(self, call, direction):
        return {"type": "object"}


class ObjParam(NameParam):
    def from_params(self, call):
        return super().from_params(call)["name"]


class QueryParam(ApiParam):
    """Read the `page` query param only: the body is never parsed."""

    def from_params(self, call):
        return {"page": call.query.get("page")}

    def to_response(self, call, result):
        return result


def _prepare_tag(call):
    call.request.update_context(http_api_test_tag=call.httprequest.headers.get("Tag"))


ROUTE = "/http_api_test"
DEFAULTS = {"type": "http_api", "auth": "public", "csrf": False}


class HttpApiTestController(http.Controller):
    @http.route(f"{ROUTE}/hello", methods=["POST"], input=NameParam(), **DEFAULTS)
    def hello(self, name):
        return {"greeting": f"Hello {name}"}

    @http.route(
        f"{ROUTE}/hello_checked",
        methods=["POST"],
        input=NameParam(),
        output=NameParam(),
        **DEFAULTS,
    )
    def hello_checked(self, name):
        if name == "bad":
            return {"nope": 1}
        return {"greeting": f"Hello {name}", "dropped": True}

    @http.route(
        f"{ROUTE}/hello_obj",
        methods=["POST"],
        input=ObjParam(),
        input_kwarg="who",
        **DEFAULTS,
    )
    def hello_obj(self, who):
        return {"greeting": f"Hello {who}"}

    @http.route(
        f"{ROUTE}/csrf",
        type="http_api",
        auth="public",
        methods=["POST"],
        csrf=True,
    )
    def csrf(self, **params):
        return {"params": params}

    @http.route(f"{ROUTE}/query_only", methods=["POST"], input=QueryParam(), **DEFAULTS)
    def query_only(self, page):
        return {"page": page}

    @http.route(f"{ROUTE}/record/<int:id>", methods=["GET"], **DEFAULTS)
    def record(self, id, **params):
        return {"id": id, "params": params}

    @http.route(f"{ROUTE}/echo", methods=["POST", "GET"], **DEFAULTS)
    def echo(self, **params):
        return {"params": {k: v for k, v in params.items() if isinstance(v, str)}}

    @http.route(f"{ROUTE}/prepare", methods=["GET"], prepare=_prepare_tag, **DEFAULTS)
    def prepare(self):
        return {"tag": request.env.context.get("http_api_test_tag")}

    @http.route(f"{ROUTE}/lang", methods=["GET"], **DEFAULTS)
    def lang(self):
        return {"lang": request.env.lang}

    @http.route(f"{ROUTE}/types", methods=["GET"], **DEFAULTS)
    def types(self):
        return {
            "date": datetime.date(2026, 1, 2),
            "datetime": datetime.datetime(2026, 1, 2, 3, 4, 5),
            "decimal": decimal.Decimal("1.5"),
        }

    @http.route(f"{ROUTE}/raw", methods=["GET"], **DEFAULTS)
    def raw(self):
        return request.make_response("raw", headers=[("Content-Type", "text/plain")])

    @http.route(f"{ROUTE}/error/<string:kind>", methods=["GET"], **DEFAULTS)
    def error(self, kind):
        errors = {
            "user": exceptions.UserError("User error"),
            "validation": exceptions.ValidationError("Validation error"),
            "missing": exceptions.MissingError("Missing"),
            "access": exceptions.AccessError("Access"),
            "boom": ValueError("Boom"),
            "conflict": ConflictError("Conflict"),
        }
        exc = errors[kind]
        if kind == "user":
            exc.rest_json_info = {"extra": "info"}
        raise exc

    @http.route(
        f"{ROUTE}/conflict",
        methods=["GET"],
        error_map=[(ConflictError, Conflict, True)],
        **DEFAULTS,
    )
    def conflict(self):
        raise ConflictError("Already there")
