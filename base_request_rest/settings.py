import calendar

from odoo import fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

API_PREFIX = '/rest'
USE_JSEND = True

def identity_func(v):
    return v

odoo_date_to_json_function = identity_func
odoo_datetime_to_json_function = identity_func
