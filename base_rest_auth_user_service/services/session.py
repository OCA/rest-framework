import datetime

from odoo import _, fields
from odoo.http import db_monodb, request, root
from odoo.service import security

from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.base_rest import restapi
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


def _restore_session(httprequest, token):
    session = root.session_store.get(token)
    if not session:
        return
    httprequest.session = session
    if httprequest.session.uid:
        httprequest.session.session_token = security.compute_session_token(
            httprequest.session, request.env
        )
        httprequest.session.modified = True
    return session


class SessionAuthenticationService(Component):
    _inherit = "base.rest.service"
    _name = "session.authenticate.service"
    _usage = "auth"
    _collection = "session.rest.services"

    @restapi.method([(["/login"], "POST")], auth="public")
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
        result["session"] = {
            "sid": request.session.sid,
            "expires_at": fields.Datetime.to_string(expiration),
        }
        return result

    @restapi.method([(["/logout"], "POST")], auth="user")
    def logout(self):
        request.session.logout(keep_db=True)
        return {"message": "Successful logout"}

    @restapi.method([(["/signup"], "POST")], auth="api_key")
    def signup(self):
        """This route will not work without a named DB, or a dbfilter"""
        params = request.params

        missing_fields = ""
        if "login" not in params:
            missing_fields += _("Login ")
        elif "name" not in params:
            missing_fields += _("Name ")
        elif "password" not in params:
            missing_fields += _("Password ")

        if missing_fields:
            return SignupError(_("Missing Fields: {}".format(missing_fields)))

        db, login, password = request.env["res.users"].sudo().signup(params)
        # as authenticate will use its own cursor we need to commit the current transaction
        request.env.cr.commit()
        #
        uid = request.session.authenticate(db, login, password)
        if not uid:
            raise SignupError(_("Authentication Failed."))
        request.env.cr.commit()

        result = request.env["ir.http"].session_info()
        # avoid to rotate the session outside of the scope of this method
        # to ensure that the session ID does not change after this method
        _rotate_session(request)
        request.session.rotate = False
        expiration = datetime.datetime.utcnow() + datetime.timedelta(days=90)
        result["session"] = {
            "sid": request.session.sid,
            "expires_at": fields.Datetime.to_string(expiration),
        }
        return result

    @restapi.method([(["/session-token"], "POST")], auth="api_key")
    def session_token(self):
        params = request.params

        if "session_id" not in params:
            return

        session = _restore_session(request, params.get("session_id"))
        if session.sid == params.get("session_id"):
            result = request.env["ir.http"].session_info()
            expiration = datetime.datetime.utcnow() + datetime.timedelta(days=90)
            result["session"] = {
                "sid": session.sid,
                "expires_at": fields.Datetime.to_string(expiration),
            }
            return result
