{
    "name": "REST API abstract attachment",
    "summary": "Add an abstract component to manage attachments",
    "version": "14.0.1.0.0",
    "website": "https://github.com/OCA/rest-framework",
    "author": "Akretion, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_rest",
        "base_rest_pydantic",
        "extendable",
    ],
    "external_dependencies": {"python": ["pydantic", "extendable_pydantic"]},
    "data": [],
}
