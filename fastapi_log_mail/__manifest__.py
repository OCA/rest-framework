# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "FastAPI Log notification",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "author": "PyTech, Odoo Community Association (OCA)",
    "maintainers": [
        "SirPyTech",
    ],
    "website": "https://github.com/OCA/rest-framework",
    "summary": "Notify logged exceptions.",
    "category": "Tools",
    "depends": [
        "fastapi_log",
        "api_log_mail",
    ],
    "data": [
        "views/fastapi_endpoint_views.xml",
    ],
}
