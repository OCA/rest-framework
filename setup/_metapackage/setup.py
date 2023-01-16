import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo-addons-oca-rest-framework",
    description="Meta package for oca-rest-framework Odoo addons",
    version=version,
    install_requires=[
        'odoo-addon-graphql_base>=16.0dev,<16.1dev',
        'odoo-addon-graphql_demo>=16.0dev,<16.1dev',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
        'Framework :: Odoo :: 16.0',
    ]
)
