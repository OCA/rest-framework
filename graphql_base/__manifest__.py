# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Graphql Base",
    "summary": """
        Base GraphQL/GraphiQL controller""",
    "version": "14.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["base"],
    "data": ["views/graphiql.xml"],
    "external_dependencies": {"python": ["graphene", "graphql_server"]},
    "development_status": "Production/Stable",
    "maintainers": ["sbidoul"],
    "installable": True,
}
