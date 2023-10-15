# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, models
from odoo.exceptions import MissingError
from odoo.osv import expression


class FastapiServiceBase(models.AbstractModel):
    _name = "fastapi.service.base"
    _description = "Fastpi Service Base can help you to expose odoo model"
    _odoo_model = None

    @property
    def _odoo_model_domain_restrict(self):
        """Restrict domain should be only used to apply some restriction
        on the record to expose.
        For example, if you do a service that expose "delivery address"
        you can return [("type", "=", "delivery")]
        The purpose of the restrict domain is not restrict the information
        dependending on the authenticated partner.
        For security restriction, use security rule.
        """
        return []

    def _convert_search_params_to_domain(self, params):
        return []

    def _search(self, paging, params=None):
        domain = expression.AND(
            [
                self._odoo_model_domain_restrict,
                self._convert_search_params_to_domain(params) if params else [],
            ]
        )
        count = self.env[self._odoo_model].search_count(domain)
        return count, self.env[self._odoo_model].search(
            domain, limit=paging.limit, offset=paging.offset
        )

    def _get(self, record_id):
        record = (
            self.env[self._odoo_model]
            .browse(record_id)
            .filtered_domain(self._odoo_model_domain_restrict)
        )
        if not record:
            raise MissingError(_("The record do not exist"))
        return record
