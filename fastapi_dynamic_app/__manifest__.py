# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Fastapi Dynamic App",
    "summary": "A Fastapi App That Provides Dynamic Router Configuration",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["fastapi"],
    "data": [
        "security/fastapi_router_security.xml",
        "views/fastapi_endpoint_views.xml",
    ],
}
