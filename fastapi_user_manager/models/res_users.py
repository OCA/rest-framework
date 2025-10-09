from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    api_key_user = fields.Char(help="Api for user crud operations")
