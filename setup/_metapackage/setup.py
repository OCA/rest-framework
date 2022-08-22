import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-rest-framework",
    description="Meta package for oca-rest-framework Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-base_rest>=15.0dev,<15.1dev',
        'odoo-addon-base_rest_auth_api_key>=15.0dev,<15.1dev',
        'odoo-addon-base_rest_auth_user_service>=15.0dev,<15.1dev',
        'odoo-addon-base_rest_datamodel>=15.0dev,<15.1dev',
        'odoo-addon-base_rest_demo>=15.0dev,<15.1dev',
        'odoo-addon-base_rest_pydantic>=15.0dev,<15.1dev',
        'odoo-addon-datamodel>=15.0dev,<15.1dev',
        'odoo-addon-extendable>=15.0dev,<15.1dev',
        'odoo-addon-model_serializer>=15.0dev,<15.1dev',
        'odoo-addon-pydantic>=15.0dev,<15.1dev',
        'odoo-addon-rest_log>=15.0dev,<15.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 15.0',
    ]
)
