{
    "name": "Fastapi users manager",
    "summary": "api for managing users in your database",
    "version": "18.0.1.0.0",
    "development_status": "Alpha",
    "category": "Tools",
    "website": "https://github.com/OCA/rest-framework",
    "author": " Akretion, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "external_dependencies": {
        "python": [],
    },
    "depends": [
        "fastapi",
        "pydantic",
    ],
    "demo": ["demo/fastapi_endpoint_demo.xml"],
    "data": [
        "views/res_users_view.xml",
        "views/fastapi_endpoint_view.xml",
        "data/endpoint.xml",
    ],
}
