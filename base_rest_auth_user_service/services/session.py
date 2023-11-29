import datetime

from odoo import fields, http
from odoo.http import request, root
from odoo.service import security

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component


class SessionAuthenticationService(Component):
    _inherit = "base.rest.service"
    _name = "session.authenticate.service"
    _usage = "auth"
    _collection = "session.rest.services"

    @restapi.method([(["/login"], "POST")], auth="public")
    def authenticate(self):
        params = request.params
        db_name = params.get("db", request.db)
        request.session.authenticate(db_name, params["login"], params["password"])
        result = request.env["ir.http"].session_info()
        # avoid to rotate the session outside of the scope of this method
        # to ensure that the session ID does not change after this method
        http.root.session_store.rotate(request.session, request.env)
        expiration = datetime.datetime.utcnow() + datetime.timedelta(seconds=http.SESSION_LIFETIME)
        result["session"] = {
            "sid": request.session.sid,
            "expires_at": fields.Datetime.to_string(expiration),
        }
        return result

    @restapi.method([(["/logout"], "POST")], auth="user")
    def logout(self):
        request.session.logout(keep_db=True)
        return {"message": "Successful logout"}
