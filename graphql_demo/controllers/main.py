# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import http
from odoo.addons.graphql_base import GraphQLControllerMixin

from ..schema import schema


class GraphQLController(http.Controller, GraphQLControllerMixin):
    @http.route("/graphiql/demo", auth="user")
    def graphiql(self, **kwargs):
        return self._handle_graphiql_request(schema)

    # optional, needed to accept application/json GraphQL requests
    # if only accepting GET/POST requests, this is not necessary
    # see also
    GraphQLControllerMixin.patch_for_json("^/graphql/demo/?$")

    @http.route("/graphql/demo", auth="user", csrf=False)
    def graphql(self, **kwargs):
        return self._handle_graphql_request(schema)
