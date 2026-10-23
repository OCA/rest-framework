# Copyright 2026 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_compute_author(
        self, author_id=None, email_from=None, raise_on_email=True
    ):
        # Use fastapi authenticated partner as author
        if self.env.context.get("authenticated_partner_id"):
            author_id = self.env.context["authenticated_partner_id"]

        author_id, email_from = super()._message_compute_author(
            author_id, email_from, raise_on_email
        )
        return author_id, email_from

    def _get_tracking_fastapi_subtype_description(self):
        endpoint = (
            self.env["fastapi.endpoint"]
            .sudo()
            .browse(self.env.context["fastapi_endpoint_id"])
        )

        return f"Via {endpoint.name}"

    def _track_subtype(self, init_values):
        if self.env.context.get("fastapi_app"):
            # Get or create the subtype for the FastAPI app
            subtype = (
                self.env["mail.message.subtype"]
                .sudo()
                .search([("name", "=", self.env.context["fastapi_app"])], limit=1)
            )
            if not subtype:
                description = self._get_tracking_fastapi_subtype_description()
                subtype = (
                    self.env["mail.message.subtype"]
                    .sudo()
                    .create(
                        {
                            "name": self.env.context["fastapi_app"],
                            "description": description,
                        }
                    )
                )
            return subtype
        return super()._track_subtype(init_values)
