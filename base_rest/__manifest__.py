# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Base Rest",
    "summary": """
        Develop your own high level REST APIs for Odoo thanks to this addon.
        """,
    "version": "19.0.1.0.0",
    "development_status": "Beta",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV, Odoo Community Association (OCA)",
    "maintainers": [],
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["bus", "component", "web", "web_tour"],
    "data": [
        "views/openapi_template.xml",
        "views/base_rest_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "base_rest/static/src/scss/base_rest.scss",
        ],
        "web.assets_tests": [
            "base_rest/static/tests/tours/**/*.js",
        ],
        "base_rest.assets_tour_openapi": [
            ("include", "web._assets_helpers"),
            ("include", "web._assets_frontend_helpers"),
            ("include", "web._assets_primary_variables"),
            ("include", "web.assets_frontend"),
            ("include", "web.assets_tests"),
        ],
    },
    "external_dependencies": {
        "python": [
            "cerberus",
            "pyquerystring",
            "parse-accept-language",
            # adding version causes missing-manifest-dependency false positives
            "apispec",
        ]
    },
}
