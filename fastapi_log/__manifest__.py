# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fastapi Log",
    "version": "16.0.1.1.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Log Fastapi requests in database",
    "category": "Tools",
    "depends": [
        "api_log",
        "fastapi",
    ],
    "website": "https://github.com/OCA/rest-framework",
    "data": [
        "views/fastapi_endpoint_views.xml",
        "views/fastapi_log_views.xml",
    ],
    "maintainers": ["paradoxxxzero"],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
}
