# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from graphene.test import Client

from odoo.tests import TransactionCase

from ..schema import schema


class TestGraphene(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super(TestGraphene, cls).setUpClass()
        cls.client = Client(schema)
        # disable logging for the graphql executor because we are testing
        # errors and OCA's test runner considers the two errors being logged
        # as fatal
        logging.getLogger("graphql.execution").setLevel(logging.CRITICAL)

    def execute(self, query):
        res = self.client.execute(query, context={"env": self.env})
        if not res:
            raise RuntimeError("GraphQL query returned no data")
        if res.get("errors"):
            raise RuntimeError(
                "GraphQL query returned error: {}".format(repr(res["errors"]))
            )
        return res.get("data")

    def test_query_all_partners(self):
        expected_names = set(self.env["res.partner"].search([]).mapped("name"))
        actual_names = {
            r["name"] for r in self.execute(" {allPartners{ name } }")["allPartners"]
        }
        self.assertEqual(actual_names, expected_names)

    def test_query_all_partners_companies_only(self):
        expected_names = set(
            self.env["res.partner"].search([("is_company", "=", True)]).mapped("name")
        )
        actual_names = {
            r["name"]
            for r in self.execute(" {allPartners(companiesOnly: true){ name } }")[
                "allPartners"
            ]
        }
        self.assertEqual(actual_names, expected_names)

    def test_error(self):
        r = self.client.execute("{errorExample}", context={"env": self.env})
        self.assertIn("UserError example", r["errors"][0]["message"])

    def test_mutation(self):
        mutation = """\
            mutation{
                createPartner(
                    name: "toto",
                    email: "toto@acsone.eu",
                ) {
                    name
                }
            }
        """
        self.client.execute(mutation, context={"env": self.env})
        self.assertEqual(
            len(self.env["res.partner"].search([("name", "=", "toto")])), 1
        )
