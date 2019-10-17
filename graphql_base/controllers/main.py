# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import re
from functools import partial

from graphql_server import (
    HttpQueryError,
    default_format_error,
    encode_execution_results,
    json_encode,
    load_json_body,
    run_http_query,
)

from odoo import http


class GraphQLControllerMixin(object):
    @staticmethod
    def patch_for_json(path_re):
        # this is to avoid Odoo, which assumes json always means json+rpc,
        # complaining about "function declared as capable of handling request
        # of type 'http' but called with a request of type 'json'"
        path_re = re.compile(path_re)
        orig_get_request = http.Root.get_request

        def get_request(self, httprequest):
            if path_re.match(httprequest.path):
                return http.HttpRequest(httprequest)
            return orig_get_request(self, httprequest)

        http.Root.get_request = get_request

    def _parse_body(self):
        req = http.request.httprequest
        # We use mimetype here since we don't need the other
        # information provided by content_type
        content_type = req.mimetype
        if content_type == "application/graphql":
            return {"query": req.data.decode("utf8")}
        elif content_type == "application/json":
            return load_json_body(req.data.decode("utf8"))
        elif content_type in (
            "application/x-www-form-urlencoded",
            "multipart/form-data",
        ):
            return http.request.params
        return {}

    def _process_request(self, schema, data):
        try:
            request = http.request.httprequest
            execution_results, all_params = run_http_query(
                schema,
                request.method.lower(),
                data,
                query_data=request.args,
                batch_enabled=False,
                catch=False,
                context={"env": http.request.env},
            )
            result, status_code = encode_execution_results(
                execution_results,
                is_batch=isinstance(data, list),
                format_error=default_format_error,
                encode=partial(json_encode, pretty=False),
            )
            headers = dict()
            headers["Content-Type"] = "application/json"
            response = http.request.make_response(result, headers=headers)
            response.status_code = status_code
            if any(er.errors for er in execution_results):
                env = http.request.env
                env.cr.rollback()
                env.clear()
            return response
        except HttpQueryError as e:
            result = json_encode({"errors": [default_format_error(e)]})
            headers = dict(e.headers)
            headers["Content-Type"] = "application/json"
            response = http.request.make_response(result, headers=headers)
            response.status_code = e.status_code
            env = http.request.env
            env.cr.rollback()
            env.clear()
            return response

    def _handle_graphql_request(self, schema):
        data = self._parse_body()
        return self._process_request(schema, data)

    def _handle_graphiql_request(self, schema):
        req = http.request.httprequest
        if req.method == "GET" and req.accept_mimetypes.accept_html:
            return http.request.render("graphql_base.graphiql", {})
        # this way of passing a GraphQL query over http is not spec compliant
        # (https://graphql.org/learn/serving-over-http/), but we use
        # this only for our GraphiQL UI, and it works with Odoo's way
        # of passing the csrf token
        return self._process_request(schema, http.request.params)
