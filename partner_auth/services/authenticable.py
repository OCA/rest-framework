# Copyright 2020 Akretion
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _
from odoo.exceptions import AccessError
from odoo.http import request

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import AbstractComponent

COOKIE_AUTH_NAME = "partner_auth"


class BaseAuthenticable(AbstractComponent):
    _inherit = "base.rest.service"
    _name = "base.authenticable"
    _usage = "auth"

    def _get_directory(self):
        raise NotImplementedError()

    def _create_partner_auth(self, params):
        directory = self._get_directory()
        return self.env["partner.auth"].sudo().register(directory, params)

    @restapi.method(
        [(["/register"], "POST")],
        input_param=Datamodel("authenticable.register.input"),
        auth="public",
    )
    def register(self, params):
        partner_auth = self._create_partner_auth(params.dump())
        return self._successfull_login(partner_auth)

    @restapi.method(
        [(["/login"], "POST")],
        input_param=Datamodel("authenticable.login.input"),
        auth="public",
    )
    def login(self, params):
        directory = self._get_directory()
        partner_auth = (
            self.env["partner.auth"]
            .sudo()
            .log_in(directory, params.login, params.password)
        )
        if partner_auth:
            return self._successfull_login(partner_auth)
        else:
            return self._invalid_login()

    def _invalid_login(self):
        raise AccessError(_("Invalid Login or Password"))

    def _successfull_login(self, partner_auth):
        data = self._prepare_login_data(partner_auth)
        response = request.make_json_response(data)
        cookie_params = partner_auth.directory_id._prepare_cookie(
            partner_auth.partner_id.id
        )
        response.set_cookie(COOKIE_AUTH_NAME, **cookie_params)
        return response

    def _prepare_login_data(self, partner_auth):
        return {"login": partner_auth.login}

    def _logout(self):
        response = request.make_json_response({})
        response.set_cookie(COOKIE_AUTH_NAME, max_age=0)
        return response

    @restapi.method(
        [(["/logout"], "POST")],
        auth="public",
    )
    def logout(self):
        return self._logout()

    @restapi.method(
        [(["/set_password"], "POST")],
        input_param=Datamodel("authenticable.set.password.input"),
        auth="public",
    )
    def set_password(self, params):
        directory = self._get_directory()
        partner_auth = (
            self.env["partner.auth"]
            .sudo()
            .set_password(directory, params.token_set_password, params.password)
        )
        return self._successfull_login(partner_auth)

    @restapi.method(
        [(["/forgot_password"], "POST")],
        input_param=Datamodel("authenticable.forget.password.input"),
        auth="public",
    )
    def forgot_password(self, params):
        directory = self._get_directory()
        self.env["partner.auth"].sudo().with_delay().forgot_password(
            directory, params.login
        )
        return {}
