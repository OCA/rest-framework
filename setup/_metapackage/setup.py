import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo14-addons-oca-rest-framework",
    description="Meta package for oca-rest-framework Odoo addons",
    version=version,
    install_requires=[
        'odoo14-addon-base_rest',
        'odoo14-addon-base_rest_auth_api_key',
        'odoo14-addon-base_rest_auth_jwt',
        'odoo14-addon-base_rest_auth_user_service',
        'odoo14-addon-base_rest_datamodel',
        'odoo14-addon-base_rest_demo',
        'odoo14-addon-datamodel',
        'odoo14-addon-extendable',
        'odoo14-addon-graphql_base',
        'odoo14-addon-graphql_demo',
        'odoo14-addon-model_serializer',
        'odoo14-addon-rest_log',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 14.0',
    ]
)
