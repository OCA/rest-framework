# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import models


class FastapiLog(models.Model):
    _inherit = "api.log"

    def log_exception(self, exception):
        res = super().log_exception(exception)
        mail_template = self.fastapi_endpoint_id.fastapi_log_mail_template_id
        if mail_template:
            mail_template.sudo().send_mail(self.id)
        return res
