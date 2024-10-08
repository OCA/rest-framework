# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Partner Auth",
    "summary": "Implements the base features for a authenticable partner",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Akretion,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/rest-framework",
    "depends": [
        "auth_signup",
        "mail",
        "queue_job",
    ],
    "data": [
        "security/res_group.xml",
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/email_data.xml",
        "views/auth_partner_view.xml",
        "views/auth_directory_view.xml",
        "views/res_partner_view.xml",
        "wizards/wizard_auth_partner_reset_password_view.xml",
    ],
    "demo": [
        "demo/res_partner_demo.xml",
        "demo/auth_directory_demo.xml",
        "demo/auth_partner_demo.xml",
    ],
    "external_dependencies": {
        "python": ["itsdangerous", "pyjwt"],
    },
}
