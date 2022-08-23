# Copyright 2021 Wakari SRL (http://www.wakari.be)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

{
    "name": "Model Serializer",
    "summary": "Automatically translate Odoo models into Datamodels "
    "for (de)serialization",
    "version": "15.0.1.2.0",
    "development_status": "Alpha",
    "license": "LGPL-3",
    "website": "https://github.com/OCA/rest-framework",
    "author": "Wakari, Odoo Community Association (OCA)",
    "maintainers": ["fdegrave"],
    "depends": ["datamodel"],
    "external_dependencies": {
        "python": [
            "marshmallow",
        ]
    },
    "data": [],
    "installable": True,
}
