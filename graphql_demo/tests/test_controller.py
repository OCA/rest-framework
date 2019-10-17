# Copyright 2018 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json

from werkzeug.urls import url_encode

from odoo.tests import HttpCase
from odoo.tests.common import HOST, PORT
from odoo.tools import mute_logger


class TestController(HttpCase):
    def url_open_json(self, url, json):
        return self.opener.post("http://{}:{}{}".format(HOST, PORT, url), json=json)

    def _check_all_partners(self, all_partners, companies_only=False):
        domain = []
        if companies_only:
            domain.append(("is_company", "=", True))
        expected_names = set(self.env["res.partner"].search(domain).mapped("name"))
        actual_names = {r["name"] for r in all_partners}
        self.assertEqual(actual_names, expected_names)

    def test_get(self):
        self.authenticate("admin", "admin")
        query = "{allPartners{name}}"
        data = {"query": query}
        r = self.url_open("/graphql/demo?" + url_encode(data))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json")
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
        self.assertEqual(r.headers["Content-Type"], "application/json")
        self._check_all_partners(r.json()["data"]["allPartners"], companies_only=True)

    def test_post_form(self):
        self.authenticate("admin", "admin")
        query = "{allPartners{name}}"
        data = {"query": query}
        r = self.url_open("/graphql/demo", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json")
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
        self.assertEqual(r.headers["Content-Type"], "application/json")
        self._check_all_partners(r.json()["data"]["allPartners"], companies_only=True)

    def test_post_json_with_variables(self):
        self.authenticate("admin", "admin")
        query = """
            query myQuery($companiesOnly: Boolean) {
                allPartners(companiesOnly: $companiesOnly) {
                    name
                }
            }
        """
        variables = {"companiesOnly": True}
        data = {"query": query, "variables": variables}
        r = self.url_open_json("/graphql/demo", data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json")
        self._check_all_partners(r.json()["data"]["allPartners"], companies_only=True)

    def test_post_form_mutation(self):
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
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json")
        self.assertEqual("Le Héro, Toto", r.json()["data"]["createPartner"]["name"])
        self.assertEqual(
            len(self.env["res.partner"].search([("email", "=", "toto@example.com")])), 1
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
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r.headers["Content-Type"], "application/json")
        self.assertIn(
            "Can only perform a mutation operation from a POST request.",
            r.json()["errors"][0]["message"],
        )

    @mute_logger("graphql.execution.executor", "graphql.execution.utils")
    def test_post_form_mutation_rollback(self):
        self.authenticate("admin", "admin")
        query = """
            mutation {
                createPartner(
                    name: "Le Héro, Toto",
                    email: "toto@example.com",
                    raiseAfterCreate: true
                ) {
                    name
                }
            }
        """
        data = {"query": query}
        r = self.url_open("/graphql/demo", data=data)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers["Content-Type"], "application/json")
        self.assertIn("as requested", r.json()["errors"][0]["message"])
        # a rollback must have occured
        self.assertEqual(
            len(self.env["res.partner"].search([("email", "=", "toto@example.com")])), 0
        )
