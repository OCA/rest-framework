# Copyright 2025 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Fastapi Auth Apikey",
    "summary": "Auhentication for FastApi using Odoo's built in apikeys",
    "version": "17.0.1.0.0",
    "website": "https://github.com/OCA/rest-framework",
    "author": "Sygel, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "fastapi",
    ],
    "data": ["views/fastapi_endpoint.xml"],
}
