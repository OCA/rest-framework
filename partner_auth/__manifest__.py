# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner Auth",
    "summary": """
        Implements the base features for a authenticable partner""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-authenticable",
    "depends": ["component", "base_rest"],
    "data": [
        "security/res_group.xml",
        "security/ir.model.access.csv",
    ],
    "demo": [],
}
