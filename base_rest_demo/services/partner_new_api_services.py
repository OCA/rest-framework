# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
from odoo.addons.base_rest import restapi
from odoo.addons.base_rest_datamodel.restapi import Datamodel
from odoo.addons.component.core import Component


class PartnerNewApiService(Component):
    _inherit = "base.rest.service"
    _name = "partner.new_api.service"
    _usage = "partner"
    _collection = "base.rest.demo.new_api.services"
    _description = """
        Partner New API Services
        Services developed with the new api provided by base_rest
    """

    @restapi.method(
        [(["/<int:id>/get", "/<int:id>"], "GET")],
        output_param=Datamodel("partner.info"),
        auth="public",
    )
    def get(self, _id):
        """
        Get partner's information
        """
        partner = self._get(_id)
        PartnerInfo = self.env.datamodels["partner.info"]
        partner_info = PartnerInfo(partial=True)
        partner_info.id = partner.id
        partner_info.name = partner.name
        partner_info.street = partner.street
        partner_info.street2 = partner.street2
        partner_info.zip_code = partner.zip
        partner_info.city = partner.city
        partner_info.phone = partner.phone
        partner_info.country = self.env.datamodels["country.info"](
            id=partner.country_id.id, name=partner.country_id.name
        )
        partner_info.state = self.env.datamodels["state.info"](
            id=partner.state_id.id, name=partner.state_id.name
        )
        partner_info.is_company = partner.is_company
        return partner_info

    @restapi.method(
        [(["/", "/search"], "GET")],
        input_param=Datamodel("partner.search.param"),
        output_param=Datamodel("partner.short.info", is_list=True),
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
        PartnerShortInfo = self.env.datamodels["partner.short.info"]
        for p in self.env["res.partner"].search(domain):
            res.append(PartnerShortInfo(id=p.id, name=p.name))
        return res

    # The following method are 'private' and should be never never NEVER call
    # from the controller.

    def _get(self, _id):
        return self.env["res.partner"].browse(_id)
