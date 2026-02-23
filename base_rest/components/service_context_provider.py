# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.addons.component.core import Component


class BaseRestServiceContextProvider(Component):
    _name = "base.rest.service.context.provider"
    _usage = "component_context_provider"

    def __init__(self, work_context):
        super().__init__(work_context)
        self.request = work_context.request
        # pylint: disable=assignment-from-none
        self.authenticated_partner_id = self._get_authenticated_partner_id()

    def _get_authenticated_partner_id(self):
        return None

    def _get_component_context(self):
        return {
            "request": self.request,
            "authenticated_partner_id": self.authenticated_partner_id,
            "collection": self.collection,
        }
