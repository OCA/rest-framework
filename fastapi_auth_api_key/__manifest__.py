# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

{
    "name": "Fastapi Auth API Key",
    "version": "18.0.1.0.0",
    "category": "Others",
    "website": "https://github.com/OCA/rest-framework",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "maintainers": ["mmequignon"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "fastapi",
        "auth_api_key_group",
    ],
    "data": [
        "views/fastapi_endpoint.xml",
    ],
}
