# -*- coding: utf-8 -*-

from odoo import models


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    def create(self, vals):
        self.clear_caches()
        return super(IrConfigParameter, self).create(vals)
