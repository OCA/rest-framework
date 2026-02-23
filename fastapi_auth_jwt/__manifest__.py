# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

{
    "name": "FastAPI Auth JWT support",
    "summary": """
        JWT bearer token authentication for FastAPI.""",
    "version": "18.0.1.0.0",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["sbidoul"],
    "website": "https://github.com/OCA/rest-framework",
    "external_dependencies": {"python": ["pyjwt", "cryptography"]},
    "depends": [
        "fastapi",
        "auth_jwt",
    ],
    "data": [],
    "demo": [],
    "installable": True,
}
