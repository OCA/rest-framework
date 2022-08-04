#  Copyright 2022 Simone Rubino - TAKOBI
#  License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import datetime

from odoo import fields
from odoo.http import db_monodb, request, root
from odoo.service import security

from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


def _rotate_session(httprequest):
    if httprequest.session.rotate:
        root.session_store.delete(httprequest.session)
        httprequest.session.sid = root.session_store.generate_key()
        if httprequest.session.uid:
            httprequest.session.session_token = security.compute_session_token(
                httprequest.session, request.env
            )
        httprequest.session.modified = True


class SessionAuthenticationService(Component):
    _inherit = "base.rest.service"
    _name = "session.authenticate.service"
    _usage = "auth"
    _collection = "session.rest.services"

    @restapi.method(
        [(["/login"], "POST")],
        auth="public",
        output_param=Datamodel('session.login'),
    )
    def authenticate(self):
        params = request.params
        db_name = params.get("db", db_monodb())
        request.session.authenticate(db_name, params["login"], params["password"])
        result = request.env["ir.http"].session_info()
        # avoid to rotate the session outside of the scope of this method
        # to ensure that the session ID does not change after this method
        _rotate_session(request)
        request.session.rotate = False
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=90)
        session_datamodel = self.env.datamodels['session']
        session = session_datamodel(
            sid=request.session.sid,
            expires_at=fields.Datetime.to_string(expiration),
        )
        session_login_datamodel = self.env.datamodels['session.login']
        session_login = session_login_datamodel(
            session=session,
            uid=result.get('uid'),
            db=result.get('db'),
        )
        return session_login

    @restapi.method(
        [(["/logout"], "POST")],
        auth="user",
        output_param=Datamodel('session.logout'),
    )
    def logout(self):
        request.session.logout(keep_db=True)
        session_logout_datamodel = self.env.datamodels['session.logout']
        session_logout = session_logout_datamodel(
            message="Successful logout",
        )
        return session_logout
