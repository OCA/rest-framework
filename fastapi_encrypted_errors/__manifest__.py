# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "FastAPI Encrypted Errors",
    "summary": "Adds encrypted error messages to FastAPI error responses.",
    "version": "16.0.1.0.1",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "maintainers": ["paradoxxxzero"],
    "website": "https://github.com/OCA/rest-framework",
    "depends": [
        "fastapi",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/fastapi_endpoint_views.xml",
        "wizards/wizard_fastapi_decrypt_errors_views.xml",
    ],
    "demo": [],
    "external_dependencies": {
        "python": ["cryptography"],
    },
}
