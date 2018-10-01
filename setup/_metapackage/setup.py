import setuptools

with open('VERSION.txt', 'r') as f:
    version = f.read().strip()

setuptools.setup(
    name="odoo10-addons-oca-rest-framework",
    description="Meta package for oca-rest-framework Odoo addons",
    version=version,
    install_requires=[
        'odoo10-addon-base_rest',
        'odoo10-addon-base_rest_demo',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Framework :: Odoo',
    ]
)
