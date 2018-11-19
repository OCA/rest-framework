# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http
from odoo.addons.graphql_base import GraphQLControllerMixin

from ..schema import schema

GRAPHIQL_PATH = "/graphiql/demo"
GRAPHQL_PATH = "/graphql/demo"

GraphQLControllerMixin.patch_for_json("^" + GRAPHQL_PATH + "/?$")


class GraphQLController(http.Controller, GraphQLControllerMixin):
    @http.route(GRAPHIQL_PATH, auth="user")
    def graphiql(self, **kwargs):
        return self._handle_graphiql_request(schema)

    @http.route(GRAPHQL_PATH, auth="api_key", csrf=False)
    def graphql(self, **kwargs):
        return self._handle_graphql_request(schema)
