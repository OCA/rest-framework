import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "external_dependencies_override": {
            "python": {"marshmallow_objects": "marshmallow-objects>=2.0.0"}
        }
    },
)
