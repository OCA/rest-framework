# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_pydantic.restapi import PydanticModel, PydanticModelList
from odoo.addons.component.core import Component

from ..pydantic_models.partner_info import PartnerInfo
from ..pydantic_models.partner_search_param import PartnerSearchParam
from ..pydantic_models.partner_short_info import PartnerShortInfo


class PartnerNewApiService(Component):
    _inherit = "base.rest.service"
    _name = "partner.pydantic.service"
    _usage = "partner_pydantic"
    _collection = "base.rest.demo.new_api.services"
    _description = """
        Partner New API Services
        Services developed with the new api provided by base_rest and pydantic
    """

    @restapi.method(
        [(["/<int:id>/get", "/<int:id>"], "GET")],
        output_param=PydanticModel(PartnerInfo),
        auth="public",
    )
    def get(self, _id):
        """
        Get partner's information
        """
        partner = self._get(_id)
        return PartnerInfo.from_orm(partner)

    @restapi.method(
        [(["/", "/search"], "GET")],
        input_param=PydanticModel(PartnerSearchParam),
        output_param=PydanticModelList(PartnerShortInfo),
        auth="public",
    )
    def search(self, partner_search_param):
        """
        Search for partners
        :param partner_search_param: An instance of partner.search.param
        :return: List of partner.short.info
        """
        domain = []
        if partner_search_param.name:
            domain.append(("name", "like", partner_search_param.name))
        if partner_search_param.id:
            domain.append(("id", "=", partner_search_param.id))
        res = []
        for p in self.env["res.partner"].sudo().search(domain):
            res.append(PartnerShortInfo.from_orm(p))
        return res

    # The following method are 'private' and should be never never NEVER call
    # from the controller.

    def _get(self, _id):
        return self.env["res.partner"].sudo().browse(_id)
