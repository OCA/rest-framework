# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.addons.component.core import AbstractComponent
from odoo.addons.base_rest import restapi
from odoo.http import request


class BaseAuthenticable(AbstractComponent):
    _inherit = "base.rest.service"
    _name = "base.authenticable"
    _usage = "auth"

    def _get_directory(self):
        raise NotImplementedError()

    def sign_up(self, payload):
        return (
            self.env[payload.backend.backend_name]
            .browse(payload.backend.backend_id)
            .sign_up(payload)
        )

    @restapi.method(
        [(["/sign_in"], "POST")],
        input_param=restapi.Datamodel("authenticable.signin.input"),
        auth="public",
    )
    def sign_in(self, params):
        directory = self._get_directory()
        partner_auth = self.env["partner.auth"].sudo().sign_in(
            directory, params.login, params.password)
        if partner_auth:
            return self._successfull_sign_in(partner_auth)
        else:
            return self._invalid_sign_in()

    def _invalid_sign_in(self):
        raise AccessError("Invalid Login or Password")

    def _successfull_sign_in(self, partner_auth):
        data = self._prepare_sign_in_data(partner_auth)
        return request.make_json_response(data)

    def _prepare_sign_in_data(self, partner_auth):
        return {"login": partner_auth.login}

    def _sign_out(self):
        return request.make_json_response({})

    @restapi.method(
        [(["/sign_out"], "POST")],
        auth="public",
    )
    def sign_out(self):
        return self._sign_out()

    @restapi.method(
        [(["/reset_password"], "POST")],
        input_param=restapi.Datamodel("authenticable.reset.password.input"),
        auth="public",
    )
    def reset_password(self, params):
        directory = self._get_directory()
        partner_auth = self.env["partner.auth"].sudo().reset_password(
            directory, params.reset_token, params.password)
        return self._successfull_sign_in(partner_auth)

    @restapi.method(
        [(["/forgot_password"], "POST")],
        input_param=restapi.Datamodel("authenticable.forget.password.input"),
        auth="public",
    )
    def forgot_password(self, params):
        directory = self._get_directory()
        self.env["partner.auth"].sudo().with_delay().forgot_password(
            directory, params.login
            )
        return {}
