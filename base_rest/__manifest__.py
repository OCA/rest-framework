# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Base Rest",
    "summary": """
        Develop your own high level REST APIs for Odoo thanks to this addon.
        """,
    "version": "15.0.1.1.0",
    "development_status": "Beta",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV, " "Odoo Community Association (OCA)",
    "maintainers": ["lmignon"],
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["component"],
    "data": [
        "views/openapi_template.xml",
        "views/base_rest_view.xml",
    ],
    "assets": {
        "web.assets_common": [
            "base_rest/static/src/scss/base_rest.scss",
            "base_rest/static/src/js/swagger_ui.js",
        ],
    },
    "demo": [],
    "external_dependencies": {
        "python": [
            "cerberus",
            "pyquerystring",
            "parse-accept-language",
            "apispec>=4.0.0",
        ]
    },
    "installable": True,
}
