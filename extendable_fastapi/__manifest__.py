# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

{
    "name": "Extendable Fastapi",
    "summary": """
        Allows the use of extendable into fastapi apps""",
    "version": "14.0.1.0.1",
    "license": "LGPL-3",
    "author": "ACSONE SA/NV,Odoo Community Association (OCA)",
    "maintainers": ["lmignon"],
    "website": "https://github.com/OCA/rest-framework",
    "depends": ["fastapi", "extendable"],
    "data": [],
    "demo": [],
    "external_dependencies": {
        "python": [
            "fastapi>=0.110.1",
            "extendable-pydantic>=0.0.4",
        ],
    },
    "installable": True,
}
