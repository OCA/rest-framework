# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fastapi Captcha Altcha Backend",
    "version": "16.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "summary": "Implement Altcha server in FastAPI",
    "category": "Tools",
    "depends": ["fastapi_captcha"],
    "website": "https://github.com/OCA/rest-framework",
    "data": [],
    "maintainers": ["paradoxxxzero"],
    "demo": [],
    "installable": True,
    "license": "AGPL-3",
    "external_dependencies": {
        "python": [
            "altcha>=2.0.0",
        ]
    },
}
