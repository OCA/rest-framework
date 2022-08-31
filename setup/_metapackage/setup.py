import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo13-addons-oca-rest-framework",
    description="Meta package for oca-rest-framework Odoo addons",
    version=version,
    install_requires=[
        'odoo13-addon-base_rest',
        'odoo13-addon-base_rest_auth_user_service',
        'odoo13-addon-base_rest_datamodel',
        'odoo13-addon-base_rest_demo',
        'odoo13-addon-base_rest_pydantic',
        'odoo13-addon-datamodel',
        'odoo13-addon-extendable',
        'odoo13-addon-graphql_base',
        'odoo13-addon-graphql_demo',
        'odoo13-addon-model_serializer',
        'odoo13-addon-pydantic',
        'odoo13-addon-rest_log',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 13.0',
    ]
)
