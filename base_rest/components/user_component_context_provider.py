# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.addons.component.core import AbstractComponent


class AbstractUserAuthenticatedPartnerProvider(AbstractComponent):
    _name = "abstract.user.authenticated.partner.provider"

    def _get_authenticated_partner_id(self):
        return self.env.user.partner_id.id
