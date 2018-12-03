# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from graphene.test import Client
from odoo.tests import TransactionCase

from ..schema import schema


class TestGraphene(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestGraphene, cls).setUpClass()
        cls.client = Client(schema)

    def execute(self, query):
        res = self.client.execute(query, context={"env": self.env})
        if not res:
            raise RuntimeError("GarphQL query returned no data")
        if res.get("error"):
            raise RuntimeError(
                "GraphQL query returned error: %s", repr(res["error"])
            )
        return res.get("data")

    def test_query_all_partners(self):
        expected_names = set(self.env["res.partner"].search([]).mapped("name"))
        actual_names = set(
            r["name"]
            for r in self.execute(" {allPartners{ name } }")["allPartners"]
        )
        self.assertEqual(actual_names, expected_names)

    def test_query_all_partners_companies_only(self):
        expected_names = set(
            self.env["res.partner"]
            .search([("is_company", "=", True)])
            .mapped("name")
        )
        actual_names = set(
            r["name"]
            for r in self.execute(
                " {allPartners(companiesOnly: true){ name } }"
            )["allPartners"]
        )
        self.assertEqual(actual_names, expected_names)
