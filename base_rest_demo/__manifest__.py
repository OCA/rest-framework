# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Base Rest Demo',
    'summary': """
        Demo addon for Base REST""",
    'version': '12.0.1.0.0',
    'development_status': 'Beta',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV, '
              'Odoo Community Association (OCA)',
    "maintainers": ['lmignon'],
    'website': 'https://acsone.eu/',
    'depends': [
        'base_rest',
        'component',
    ],
    'data': [
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [
            'jsondiff'
        ],
    },
}
