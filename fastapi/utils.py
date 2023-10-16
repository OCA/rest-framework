# Copyright 2023 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo import _, models
from odoo.exceptions import MissingError
from odoo.osv import expression


class FilteredDomainAdapter:
    def __init__(self, model: models.BaseModel, base_domain: list):
        self._model = model
        self._base_domain = base_domain

    def get(self, record_id: int) -> models.BaseModel:
        record = self._model.browse(record_id).filtered_domain(self._base_domain)
        if record:
            return record
        else:
            raise MissingError(_("The record do not exist"))

    def search_with_count(self, domain: list, limit, offset):
        domain = expression.AND([self._base_domain, domain])

        count = self._model.search_count(domain)
        return count, self._model.search(domain, limit=limit, offset=offset)
