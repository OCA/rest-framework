# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Graphql Base",
    "summary": """
        Base GraphQL/GraphiQL controller""",
    "version": "13.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["base"],
    "data": ["views/graphiql.xml"],
    "external_dependencies": {"python": ["graphene", "graphql-server-core"]},
    "development_status": "Beta",
    "maintainers": ["sbidoul"],
    "installable": True,
}
