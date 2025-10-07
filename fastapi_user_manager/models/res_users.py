from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    api_key_user = fields.Char(string="Api for connecting sacpa")
