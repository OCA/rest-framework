# Copyright 2024 Akretion (http://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request


class AuthPartner(models.Model):
    _inherit = "auth.partner"

    def local_impersonate(self):
        """Local impersonate for dev mode"""
        self.ensure_one()

        if not self.env.user._is_admin():
            raise AccessDenied(_("Only admin can impersonate locally"))

        if not hasattr(request, "future_response"):
            raise UserError(
                _("Please install base_future_response for local impersonate to work")
            )

        for endpoint in self.directory_id.fastapi_endpoint_ids:
            helper = self.env["fastapi.auth.service"].new({"endpoint_id": endpoint})
            helper._set_auth_cookie(self, request.future_response)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Impersonation successful"),
                "message": _("You are now impersonating %s\n%%s") % self.login,
                "links": [
                    {
                        "label": f"{endpoint.app.title()} api docs",
                        "url": endpoint.docs_url,
                    }
                    for endpoint in self.directory_id.fastapi_endpoint_ids
                ],
                "type": "success",
                "sticky": False,
            },
        }

    def _get_impersonate_url(self, token, **kwargs):
        endpoint = kwargs.get("endpoint")
        if not endpoint:
            return super()._get_impersonate_url(token, **kwargs)

        base = (
            endpoint.public_api_url
            or endpoint.public_url
            or (
                self.env["ir.config_parameter"].sudo().get_param("web.base.url")
                + endpoint.root_path
            )
        )
        return f"{base.rstrip('/')}/auth/impersonate/{token}"

    def _get_impersonate_action(self, token, **kwargs):
        # Get the endpoint from a wizard
        endpoint_id = self.env.context.get("fastapi_endpoint_id")
        endpoint = None

        if endpoint_id:
            endpoint = self.env["fastapi.endpoint"].browse(endpoint_id)

        if not endpoint:
            endpoints = self.directory_id.fastapi_endpoint_ids
            if len(endpoints) == 1:
                endpoint = endpoints
            else:
                wizard = self.env["ir.actions.act_window"]._for_xml_id(
                    "fastapi_auth_partner.auth_partner_action_impersonate"
                )
                wizard["context"] = {"default_auth_partner_id": self.id}
                return wizard

        return super()._get_impersonate_action(token, endpoint=endpoint, **kwargs)
