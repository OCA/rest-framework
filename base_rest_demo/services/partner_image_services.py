# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import base64

from odoo import _
from odoo.exceptions import MissingError
from odoo.http import request

from odoo.addons.base_rest.components.service import skip_secure_response
from odoo.addons.component.core import Component


class PartnerImageService(Component):
    _inherit = "base.rest.service"
    _name = "partner_image.service"
    _usage = "partner_image"
    _collection = "base.rest.demo.private.services"
    _description = """
        Partner Image Services

        Service used to retrieve the partner's image
        Access to the partner image service is only allowed to authenticated
        users.
        If you are not authenticated go to <a href='/web/login'>Login</a>
    """

    @skip_secure_response
    def get(self, _id, size):
        """
        Get partner's image
        """
        field = "image"
        if size == "small":
            field = "image_small"
        elif size == "medium":
            field = "image_medium"
        status, headers, content = self.env["ir.http"].binary_content(
            model="res.partner", id=_id, field=field
        )
        if not content:
            raise MissingError(_("No image found for partner %s") % _id)
        image_base64 = base64.b64decode(content)
        headers.append(("Content-Length", len(image_base64)))
        response = request.make_response(image_base64, headers)
        response.status_code = status
        return response

    # Validator
    def _validator_get(self):
        return {
            "size": {
                "type": "string",
                "required": False,
                "default": "small",
                "allowed": ["small", "medium", "large"],
            }
        }
