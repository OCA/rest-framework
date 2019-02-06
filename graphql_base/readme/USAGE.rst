To use this module, you need to

- create your graphene schema
- create your controller to expose your GraphQL endpoint,
  and optionally a GraphiQL IDE.

This module does not attempt to expose the whole Odoo object model.
This could be the purpose of another module based on this one.
We believe however that it is preferable to expose a specific well tested
endpoint for each customer, so as to reduce coupling by knowing precisely
what is exposed and needs to be tested when upgrading Odoo.

To start working with this module, we recommend the following approach:

- Learn `GraphQL basics <https://graphql.org/learn/>`__
- Learn `graphene <https://graphene-python.org/>`__, the python library
  used to create GraphQL schemas and resolvers.
- Examine the ``graphql_demo`` module in this repo, copy it,
  adapt the controller to suit your needs (routes, authentication methods).
- Start building your own schema and resolver.

Building your schema
~~~~~~~~~~~~~~~~~~~~

The schema can be built using native graphene types.
An ``odoo.addons.graphql_base.types.OdooObjectType``
is provided as a convenience. It is a graphene ``ObjectType`` with a
default attribute resolver which:

- converts False to None (except for Boolean types), to avoid Odoo's weird
  ``False`` strings being rendered as json ``"false"``;
- adds the user timezone to Datetime fields;
- raises an error if an attribute is absent to avoid field name typing errors.

Creating GraphQL controllers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The module provides an ``odoo.addons.graphql_base.GraphQLControllerMixin``
class to help you build GraphQL controllers providing GraphiQL and/or GraphQL
endpoints.

.. code-block:: python

    from odoo import http
    from odoo.addons.graphql_base import GraphQLControllerMixin

    from ..schema import schema


    class GraphQLController(http.Controller, GraphQLControllerMixin):

        # The GraphiQL route, providing an IDE for developers
        @http.route("/graphiql/demo", auth="user")
        def graphiql(self, **kwargs):
            return self._handle_graphiql_request(schema)

        # Optional monkey patch, needed to accept application/json GraphQL
        # requests. If you only need to accept GET requests or POST
        # with application/x-www-form-urlencoded content,
        # this is not necessary.
        GraphQLControllerMixin.patch_for_json("^/graphql/demo/?$")

        # The graphql route, for applications.
        # Note csrf=False: you may want to apply extra security
        # (such as origin restrictions) to this route.
        @http.route("/graphql/demo", auth="user", csrf=False)
        def graphql(self, **kwargs):
            return self._handle_graphql_request(schema)
