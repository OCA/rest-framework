# Copyright 2021 Wakari SRL (http://www.wakari.be)
# Copyright 2022 Simone Rubino - TAKOBI
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "REST Authentication Service",
    "summary": "Login/logout from session using a REST call",
    "version": "12.0.1.0.0",
    "development_status": "Alpha",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/rest-framework",
    "author": "Wakari, Odoo Community Association (OCA)",
    "depends": [
        "base_rest",
        "base_rest_datamodel",
    ],
    "external_dependencies": {
        "python": [
            "marshmallow",
        ],
    },
    "data": [],
}
