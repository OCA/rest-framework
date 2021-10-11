# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.addons.component.core import Component


class PingJwtService(Component):
    _inherit = "ping.service"
    _name = "ping.jwt.service"
    _collection = "base.rest.demo.jwt.services"
