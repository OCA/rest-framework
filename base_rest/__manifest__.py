# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Base Rest",
    "summary": """
        Develop your own high level REST APIs for Odoo thanks to this addon.
        """,
    "version": "16.0.1.0.2",
    "development_status": "Beta",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV, " "Odoo Community Association (OCA)",
    "maintainers": [],
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["component", "web"],
    "data": [
        "views/openapi_template.xml",
        "views/base_rest_view.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "base_rest/static/src/scss/base_rest.scss",
            "base_rest/static/src/js/swagger_ui.js",
            "base_rest/static/src/js/swagger.js",
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
    "installable": True,
}
