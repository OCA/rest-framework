# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
from werkzeug.urls import url_encode

from odoo.tests import HttpCase


class TestController(HttpCase):
    def _check_all_partners(self, all_partners, companies_only=False):
        domain = []
        if companies_only:
            domain.append(("is_company", "=", True))
        expected_names = set(
            self.env["res.partner"].search(domain).mapped("name")
        )
        actual_names = set(r["name"] for r in all_partners)
        self.assertEqual(actual_names, expected_names)

    def test_get(self):
        self.authenticate("admin", "admin")
        query = "{allPartners{name}}"
        data = {"query": query}
        r = self.url_open("/graphql/demo?" + url_encode(data))
        self.assertEqual(r.status_code, 200)
        self._check_all_partners(r.json()["data"]["allPartners"])

    def test_get_with_variables(self):
        self.authenticate("admin", "admin")
        query = """
            query myQuery($companiesOnly: Boolean) {
                allPartners(companiesOnly: $companiesOnly) {
                    name
                }
            }
        """
        variables = {"companiesOnly": True}
        data = {"query": query, "variables": json.dumps(variables)}
        r = self.url_open("/graphql/demo?" + url_encode(data))
        self.assertEqual(r.status_code, 200)
        self._check_all_partners(
            r.json()["data"]["allPartners"], companies_only=True
        )

    def test_post_form(self):
        self.authenticate("admin", "admin")
        query = "{allPartners{name}}"
        data = {"query": query}
        r = self.url_open("/graphql/demo", data=data)
        self.assertEqual(r.status_code, 200)
        self._check_all_partners(r.json()["data"]["allPartners"])

    def test_post_form_with_variables(self):
        self.authenticate("admin", "admin")
        query = """
            query myQuery($companiesOnly: Boolean) {
                allPartners(companiesOnly: $companiesOnly) {
                    name
                }
            }
        """
        variables = {"companiesOnly": True}
        data = {"query": query, "variables": json.dumps(variables)}
        r = self.url_open("/graphql/demo", data=data)
        self.assertEqual(r.status_code, 200)
        self._check_all_partners(
            r.json()["data"]["allPartners"], companies_only=True
        )

    def test_post_mutation(self):
        self.authenticate("admin", "admin")
        query = """
            mutation {
                createPartner(
                    name: "Le Héro, Toto", email: "toto@example.com"
                ) {
                    name
                }
            }
        """
        data = {"query": query}
        r = self.url_open("/graphql/demo", data=data)
        assert r.status_code == 200
        self.assertEqual(
            "Le Héro, Toto", r.json()["data"]["createPartner"]["name"]
        )

    def test_get_mutation_not_allowed(self):
        """
        Cannot perform a mutation with a GET, must use POST.
        """
        self.authenticate("admin", "admin")
        query = """
            mutation {
                createPartner(
                    name: "Le Héro, Toto", email: "toto@example.com"
                ) {
                    name
                }
            }
        """
        data = {"query": query}
        r = self.url_open("/graphql/demo?" + url_encode(data))
        assert r.status_code == 500
