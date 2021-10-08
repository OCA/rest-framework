import datetime

from odoo import fields
from odoo.http import db_monodb, request, root
from odoo.service import security

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
