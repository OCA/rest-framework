# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class APILog(models.Model):
    _name = "api.log"
    _inherit = [
        "api.log",
        "mail.activity.mixin",
        # mail.thread is needed
        # because message_subscribe is called
        # during activity creation
        "mail.thread",
    ]
    _mail_post_access = "read"  # Access required to open an activity

    @api.model
    def log_request(self, request, override_log_values=None):
        return super(
            APILog,
            self.with_context(tracking_disable=True),
        ).log_request(request, override_log_values=override_log_values)

    def _notify_api_log_exception(self):
        if collection := self.collection_ref:
            activity_type = collection.api_log_mail_exception_activity_type_id
            if activity_type:
                self.sudo().activity_schedule(
                    activity_type_id=activity_type.id,
                )

            mail_template = collection.api_log_mail_exception_template_id
            if mail_template:
                mail_template.sudo().send_mail(self.id)

    def log_exception(self, exception):
        res = super().log_exception(exception)
        self._notify_api_log_exception()
        return res
