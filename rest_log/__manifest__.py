# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "REST Log",
    "summary": "Track REST API calls into DB",
    "version": "18.0.1.0.1",
    "development_status": "Beta",
    "website": "https://github.com/OCA/rest-framework",
    "author": "Camptocamp, ACSONE, Odoo Community Association (OCA)",
    "maintainers": ["simahawk"],
    "license": "LGPL-3",
    "depends": ["base_rest"],
    "data": [
        "data/ir_config_parameter_data.xml",
        "data/ir_cron_data.xml",
        "security/groups.xml",
        "security/ir.model.access.csv",
        "views/rest_log_views.xml",
        "views/menu.xml",
    ],
}
