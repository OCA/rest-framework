# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Base Rest',
    'summary': """
        Base addon to implement REST service in an efficient and secured
        way""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'ACSONE SA/NV,Odoo Community Association (OCA)',
    'website': 'https://acsone.eu/',
    'depends': [
        'component'
    ],
    'data': [
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
