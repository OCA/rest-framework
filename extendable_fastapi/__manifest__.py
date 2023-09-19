# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Extendable Fastapi",
    "summary": """
        Allows the use of extendable into fastapi apps""",
    "version": "16.0.2.0.2",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["lmignon"],
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["fastapi", "extendable"],
    "data": [],
    "demo": [],
    "external_dependencies": {
        "python": [
            "pydantic>=2.0.0",
            "extendable-pydantic>=1.1.0",
        ],
    },
    "installable": True,
}
