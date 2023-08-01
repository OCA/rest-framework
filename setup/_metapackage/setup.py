import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-rest-framework",
    description="Meta package for oca-rest-framework Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_rest>=16.0dev,<16.1dev',
        'odoo-addon-base_rest_auth_api_key>=16.0dev,<16.1dev',
        'odoo-addon-base_rest_datamodel>=16.0dev,<16.1dev',
        'odoo-addon-base_rest_demo>=16.0dev,<16.1dev',
        'odoo-addon-base_rest_pydantic>=16.0dev,<16.1dev',
        'odoo-addon-datamodel>=16.0dev,<16.1dev',
        'odoo-addon-extendable>=16.0dev,<16.1dev',
        'odoo-addon-extendable_fastapi>=16.0dev,<16.1dev',
        'odoo-addon-fastapi>=16.0dev,<16.1dev',
        'odoo-addon-fastapi_auth_jwt>=16.0dev,<16.1dev',
        'odoo-addon-fastapi_auth_jwt_demo>=16.0dev,<16.1dev',
        'odoo-addon-graphql_base>=16.0dev,<16.1dev',
        'odoo-addon-graphql_demo>=16.0dev,<16.1dev',
        'odoo-addon-pydantic>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
