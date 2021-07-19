# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).


from odoo.addons.component.core import Component


class BaseRestServiceContextProvider(Component):
    _name = "base.rest.service.context.provider"
    _usage = "component_context_provider"

    @property
    def request(self):
        return self.work.request

    def _get_component_context(self):
        return {"request": self.request}
