# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Test Extendable Pydantic Fastapi",
    "summary": """
        Tests integration between extendable_pydantic/odoo_addon_fastapi and
        odoo_addon_extendable_fastapi""",
    "version": "16.0.2.0.1",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": [
        "fastapi",
        "extendable_fastapi",
    ],
    "data": [],
    "demo": [],
    "external_dependencies": {
        "python": [
            "pydantic>=2.0.0",
            "extendable-pydantic>=1.0.0",
        ]
    },
}
