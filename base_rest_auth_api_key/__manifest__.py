# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "Base Rest Auth Api Key",
    "summary": """
        Base Rest: Add support for the auth_api_key security policy into the
        openapi documentation""",
    "version": "14.0.1.0.1",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["base_rest", "auth_api_key"],
    "maintainers": ["lmignon"],
    "installable": True,
    "auto_install": True,
    "external_dependencies": {
        "python": [
            "apispec>=4.0.0",
        ]
    },
}
