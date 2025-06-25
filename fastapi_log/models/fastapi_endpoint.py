# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class FastapiEndpoint(models.Model):
    _name = "fastapi.endpoint"
    _inherit = [
        "api.log_collection.mixin",
        "fastapi.endpoint",
    ]
