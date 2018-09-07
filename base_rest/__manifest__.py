# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Base Rest',
    'summary': """
        Develop your own high level REST APIs for Odoo thanks to this addon.
        """,
    'version': '10.0.1.0.0',
    "development_status": "Beta",
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV, '
              'Odoo Community Association (OCA)',
    "maintainers": ['lmignon'],
    "website": "https://github.com/OCA/rest-framework",
    'depends': [
        'component'
    ],
    'data': [
        'views/assets_template.xml',
        'views/openapi_template.xml',
        'views/base_rest_view.xml',
    ],
    'demo': [
    ],
    'external_dependencies': {
        'python': [
            'cerberus',
            'pyquerystring',
            'accept_language'
        ],
    },
}
