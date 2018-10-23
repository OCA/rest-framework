import calendar
import datetime

from odoo import fields


def odoo_datetime_to_unix_timestamp(odoo_datetime):
    return calendar.timegm(
        fields.Datetime.from_string(odoo_datetime).timetuple())

def unix_timestamp_to_odoo_datetime(timestamp):
    return fields.Datetime.to_string(datetime.datetime.utcfromtimestamp(timestamp))
