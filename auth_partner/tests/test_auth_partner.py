# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from contextlib import contextmanager
from datetime import datetime, timedelta

from freezegun import freeze_time

from odoo.exceptions import AccessDenied, UserError

from .common import CommonTestAuthPartner


class TestAuthPartner(CommonTestAuthPartner):
    @contextmanager
    def assert_no_new_mail(self):
        with self.new_mails() as new_mails:
            yield
        self.assertFalse(new_mails)

    def test_default_secret_key(self):
        self.assertGreaterEqual(len(self.directory.secret_key), 64)

    def test_login_ok(self):
        with self.assert_no_new_mail():
            auth_partner = self.env["auth.partner"]._login(
                self.directory,
                login="partner-auth@example.org",
                password="Super-secret$1",
            )
        self.assertTrue(auth_partner)

    def test_login_wrong_password(self):
        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.directory, login="partner-auth@example.org", password="wrong"
            )

    def test_login_mail_not_verified(self):
        self.directory.force_verified_email = True
        with self.assertRaisesRegex(AccessDenied, "Email address not validated"):
            self.env["auth.partner"]._login(
                self.directory,
                login="partner-auth@example.org",
                password="Super-secret$1",
            )

    def test_login_wrong_login(self):
        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.directory,
                login="partner-auth@example.com",
                password="Super-secret$1",
            )

    def test_login_wrong_directory(self):
        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.other_directory,
                login="partner-auth@example.com",
                password="Super-secret$1",
            )

    def test_signup(self):
        with self.new_mails() as new_mails:
            new_auth_partner = self.env["auth.partner"]._signup(
                self.directory,
                name="New Partner",
                login="new-partner-auth@example.org",
                password="NewSecret",
            )
        self.assertTrue(new_auth_partner)
        # Ensure we can't read the password
        self.assertNotEqual(new_auth_partner.password, "NewSecret")

        self.assertEqual(len(new_mails), 1)
        self.assertEqual(new_mails.subject, "Welcome")
        self.assertIn("Welcome to the site, please", new_mails.body)

        auth_partner = self.env["auth.partner"]._login(
            self.directory, login="new-partner-auth@example.org", password="NewSecret"
        )
        self.assertTrue(auth_partner)
        self.assertEqual(auth_partner, new_auth_partner)

    def test_signup_wrong_directory(self):
        new_auth_partner = self.env["auth.partner"]._signup(
            self.other_directory,
            name="New Partner",
            login="new-partner-auth@example.org",
            password="NewSecret",
        )
        self.assertTrue(new_auth_partner)

        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.directory,
                login="new-partner-auth@example.org",
                password="NewSecret",
            )

    def test_signup_same_login_other_directory(self):
        new_auth_partner = self.env["auth.partner"]._signup(
            self.directory,
            name="New Partner",
            login="new-partner-auth@example.org",
            password="NewSecret",
        )
        self.assertTrue(new_auth_partner)
        new_auth_partner_2 = self.env["auth.partner"]._signup(
            self.other_directory,
            name="New Partner",
            login="new-partner-auth@example.org",
            password="NewSecret2",
        )
        self.assertTrue(new_auth_partner_2)
        self.assertNotEqual(new_auth_partner, new_auth_partner_2)

        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.directory,
                login="new-partner-auth@example.org",
                password="NewSecret2",
            )

        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.other_directory,
                login="new-partner-auth@example.org",
                password="NewSecret",
            )

    def test_validate_email_ok(self):
        self.assertFalse(self.auth_partner.mail_verified)
        token = self.auth_partner._generate_validate_email_token()
        self.auth_partner._validate_email(self.directory, token)
        self.assertTrue(self.auth_partner.mail_verified)

    def test_validate_email_required_login(self):
        self.directory.force_verified_email = True
        token = self.auth_partner._generate_validate_email_token()
        self.auth_partner._validate_email(self.directory, token)
        with self.assert_no_new_mail():
            auth_partner = self.env["auth.partner"]._login(
                self.directory,
                login="partner-auth@example.org",
                password="Super-secret$1",
            )
        self.assertTrue(auth_partner)

    def test_validate_email_wrong_token(self):
        self.assertFalse(self.auth_partner.mail_verified)
        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.auth_partner._validate_email(self.directory, "wrong")
        self.assertFalse(self.auth_partner.mail_verified)

    def test_validate_email_token(self):
        with self.new_mails() as new_mails:
            new_auth_partner = self.env["auth.partner"]._signup(
                self.directory,
                name="New Partner",
                login="new-partner-auth@example.org",
                password="NewSecret",
            )
        self.assertFalse(new_auth_partner.mail_verified)
        token = new_mails.body.split("token=")[1].split('">')[0]
        new_auth_partner._validate_email(self.directory, token)
        self.assertTrue(new_auth_partner.mail_verified)

    def test_impersonate_ok(self):
        action = self.auth_partner.with_user(
            self.env.ref("base.user_admin")
        ).impersonate()
        token = action["url"].split("/")[-1]

        auth_partner = self.env["auth.partner"]._impersonating(self.directory, token)
        self.assertEqual(auth_partner, self.auth_partner)

    def test_impersonate_once(self):
        action = self.auth_partner.with_user(
            self.env.ref("base.user_admin")
        ).impersonate()
        token = action["url"].split("/")[-1]

        self.env["auth.partner"]._impersonating(self.directory, token)
        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.env["auth.partner"]._impersonating(self.directory, token)

    def test_impersonate_wrong_directory(self):
        action = self.auth_partner.with_user(
            self.env.ref("base.user_admin")
        ).impersonate()
        token = action["url"].split("/")[-1]

        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.env["auth.partner"]._impersonating(self.other_directory, token)

    def test_impersonate_wrong_user(self):
        with self.assertRaisesRegex(AccessDenied, "not allowed to impersonate"):
            self.auth_partner.with_user(self.env.ref("base.default_user")).impersonate()

    def test_impersonate_not_expired_token(self):
        self.directory.impersonating_token_duration = 100
        action = self.auth_partner.with_user(
            self.env.ref("base.user_admin")
        ).impersonate()
        token = action["url"].split("/")[-1]

        with freeze_time(datetime.now() + timedelta(hours=1)):
            self.env["auth.partner"]._impersonating(self.directory, token)

    def test_impersonate_expired_token(self):
        self.directory.impersonating_token_duration = 100
        action = self.auth_partner.with_user(
            self.env.ref("base.user_admin")
        ).impersonate()
        token = action["url"].split("/")[-1]

        with freeze_time(datetime.now() + timedelta(hours=2)), self.assertRaisesRegex(
            UserError, "Invalid Token"
        ):
            self.env["auth.partner"]._impersonating(self.directory, token)

    def test_set_password_ok(self):
        self.auth_partner._set_password(
            self.directory,
            self.auth_partner._generate_set_password_token(),
            "ResetSecret",
        )
        auth_partner = self.env["auth.partner"]._login(
            self.directory, login="partner-auth@example.org", password="ResetSecret"
        )
        self.assertTrue(auth_partner)

    def test_set_password_wrong_token(self):
        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.auth_partner._set_password(self.directory, "wrong", "ResetSecret")

    def test_set_password_once(self):
        token = self.auth_partner._generate_set_password_token()
        self.auth_partner._set_password(self.directory, token, "ResetSecret")
        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.auth_partner._set_password(self.directory, token, "ResetSecret")

    def test_set_password_not_expired_token(self):
        self.directory.set_password_token_duration = 100
        token = self.auth_partner._generate_set_password_token()

        with freeze_time(datetime.now() + timedelta(hours=1)):
            self.auth_partner._set_password(self.directory, token, "ResetSecret")

        auth_partner = self.env["auth.partner"]._login(
            self.directory, login="partner-auth@example.org", password="ResetSecret"
        )
        self.assertTrue(auth_partner)

    def test_set_password_expired_token(self):
        self.directory.set_password_token_duration = 100
        token = self.auth_partner._generate_set_password_token()

        with freeze_time(datetime.now() + timedelta(hours=2)), self.assertRaisesRegex(
            UserError, "Invalid Token"
        ):
            self.auth_partner._set_password(self.directory, token, "ResetSecret")

    def test_reset_password_ok(self):
        with self.new_mails() as new_mails:
            self.auth_partner._request_reset_password()
        self.assertEqual(len(new_mails), 1)
        self.assertEqual(new_mails.subject, "Reset Password")
        self.assertIn(
            "Click on the following link to reset your password", new_mails.body
        )

        token = new_mails.body.split("token=")[1].split('">')[0]
        self.auth_partner._set_password(self.directory, token, "ResetSecret")
        auth_partner = self.env["auth.partner"]._login(
            self.directory, login="partner-auth@example.org", password="ResetSecret"
        )
        self.assertTrue(auth_partner)

    def test_reset_password_wrong_partner(self):
        with self.new_mails() as new_mails:
            self.auth_partner._request_reset_password()
        self.assertEqual(len(new_mails), 1)
        self.assertEqual(new_mails.subject, "Reset Password")
        self.assertIn(
            "Click on the following link to reset your password", new_mails.body
        )

        token = new_mails.body.split("token=")[1].split('">')[0]
        # This should probably raise instead of reseting the auth_partner password
        self.other_auth_partner._set_password(self.directory, token, "ResetSecret")
        with self.assertRaisesRegex(AccessDenied, "Invalid Login or Password"):
            self.env["auth.partner"]._login(
                self.directory,
                login="other-partner-auth@example.org",
                password="ResetSecret",
            )

    def test_reset_password_once(self):
        with self.new_mails() as new_mails:
            self.auth_partner._request_reset_password()
        self.assertEqual(len(new_mails), 1)
        self.assertEqual(new_mails.subject, "Reset Password")
        token = new_mails.body.split("token=")[1].split('">')[0]
        self.auth_partner._set_password(self.directory, token, "ResetSecret")

        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.auth_partner._set_password(self.directory, token, "ResetSecret2")

    def test_send_invite_set_password_ok(self):
        with self.new_mails() as new_mails:
            self.auth_partner._send_invite()
        self.assertEqual(len(new_mails), 1)
        self.assertEqual(new_mails.subject, "Welcome")
        self.assertIn("your account have been created", new_mails.body)
        token = new_mails.body.split("token=")[1].split('">')[0]

        self.auth_partner._set_password(self.directory, token, "ResetSecret")
        auth_partner = self.env["auth.partner"]._login(
            self.directory, login="partner-auth@example.org", password="ResetSecret"
        )
        self.assertTrue(auth_partner)

    def test_send_invite_set_password_once(self):
        with self.new_mails() as new_mails:
            self.auth_partner._send_invite()
        self.assertEqual(len(new_mails), 1)
        self.assertEqual(new_mails.subject, "Welcome")

        token = new_mails.body.split("token=")[1].split('">')[0]
        self.auth_partner._set_password(self.directory, token, "ResetSecret")

        with self.assertRaisesRegex(UserError, "Invalid Token"):
            self.auth_partner._set_password(self.directory, token, "ResetSecret2")
