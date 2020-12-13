# Copyright 2020 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models



class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_auth_ids = fields.One2many(
        'partner.auth',
        'partner_id',
        'Partner Auth')
