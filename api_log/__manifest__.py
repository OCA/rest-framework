# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "API Log",
    "version": "16.0.1.0.0",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "summary": "Log API requests in database",
    "category": "Tools",
    "depends": ["web"],
    "website": "https://github.com/OCA/rest-framework",
    "data": [
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "views/api_log_views.xml",
    ],
    "maintainers": ["paradoxxxzero"],
}
