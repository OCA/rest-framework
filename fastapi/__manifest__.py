# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

{
    "name": "Odoo FastAPI",
    "summary": """
        Odoo FastApi instegration""",
    "version": "16.0.0.0.1",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["lmignon"],
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["endpoint_route_handler"],
    "data": [
        "security/res_groups.xml",
        "security/fastapi_app.xml",
        "views/fastapi_menu.xml",
        "views/fastapi_app.xml",
    ],
    "demo": ["demo/fastapi_app_demo.xml"],
    "external_dependencies": {
        "python": ["fastapi", "python-multipart", "ujson", "a2wsgi"]
    },
}
