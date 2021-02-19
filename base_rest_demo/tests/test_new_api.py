# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from .common import NewServiceCommonCase


class TestPartner(NewServiceCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = cls._get_service("partner")

    def test_search(self):
        self.env["res.partner"].create([{"name": f"P{idx}"} for idx in range(0, 1000)])
        self.service.dispatch("search")

    def test_multiple_search(self):
        self.env["res.partner"].create({"name": "P"})
        for _idx in range(0, 1000):
            self.service.dispatch("search")
