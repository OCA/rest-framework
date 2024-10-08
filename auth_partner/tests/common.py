# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from typing import Any

from odoo.tests.common import TransactionCase

from odoo.addons.mail.tests.common import MockEmail


class CommonTestAuthPartner(TransactionCase, MockEmail):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, queue_job__no_delay=True))

        cls.partner = cls.env.ref("auth_partner.res_partner_auth_demo")
        cls.other_partner = cls.partner.copy(
            {"name": "Other Partner", "email": "other-partner-auth@example.org"}
        )
        cls.auth_partner = cls.partner.auth_partner_ids

        cls.directory = cls.env.ref("auth_partner.demo_directory")
        cls.directory.impersonating_user_ids = cls.env.ref("base.user_admin")

        cls.other_auth_partner = cls.env["auth.partner"].create(
            {
                "login": cls.other_partner.email,
                "password": "Super-secret3",
                "directory_id": cls.directory.id,
                "partner_id": cls.other_partner.id,
            }
        )
        cls.other_directory = cls.directory.copy({"name": "Other Directory"})

    @contextmanager
    def new_mails(self):
        mailmail = self.env["mail.mail"]

        class MailsProxy(mailmail.__class__):
            __slots__ = ["_prev", "__weakref__"]

            def __init__(self):
                object.__setattr__(self, "_prev", mailmail.search([]))

            def __getattribute__(self, name: str) -> Any:
                mails = mailmail.search([]) - object.__getattribute__(self, "_prev")
                return object.__getattribute__(mails, name)

        new_mails = MailsProxy()
        with self.mock_mail_gateway():
            yield new_mails

    @contextmanager
    def assert_no_new_mail(self):
        with self.new_mails() as new_mails:
            yield
        self.assertFalse(new_mails)
