# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# from urllib.parse import urlparse


from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.base_rest.tests.common import TransactionRestServiceRegistryCase
from odoo.addons.component.tests.common import new_rollbacked_env
from odoo.addons.rest_log import exceptions as log_exceptions  # pylint: disable=W7950

from .common import FakeConcurrentUpdateError, TestDBLoggingMixin


class TestDBLoggingExceptionBase(
    TransactionRestServiceRegistryCase, TestDBLoggingMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)

    @classmethod
    def tearDownClass(cls):
        # pylint: disable=W8110
        cls._teardown_registry(cls)
        super().tearDownClass()

    def _test_exception(self, test_type, wrapping_exc, exc_name, severity):
        log_model = self.env["rest.log"].sudo()
        initial_entries = log_model.search([])
        entry_url_from_exc = None
        # Context: we are running in a transaction case which uses savepoints.
        # The log machinery is going to rollback the transation when catching errors.
        # Hence we need a completely separated env for the service.
        with new_rollbacked_env() as new_env:
            # Init fake collection w/ new env
            collection = _PseudoCollection(self._collection_name, new_env)
            service = self._get_service(self, collection=collection)
            with self._get_mocked_request(env=new_env):
                try:
                    service.dispatch("fail", test_type)
                except Exception as err:
                    # Not using `assertRaises` to inspect the exception directly
                    self.assertTrue(isinstance(err, wrapping_exc))
                    self.assertEqual(
                        service._get_exception_message(err), "Failed as you wanted!"
                    )
                    entry_url_from_exc = err.rest_json_info["log_entry_url"]

        with new_rollbacked_env() as new_env:
            log_model = new_env["rest.log"].sudo()
            entry = log_model.search([]) - initial_entries
            expected = {
                "collection": service._collection,
                "state": "failed",
                "result": "null",
                "exception_name": exc_name,
                "exception_message": "Failed as you wanted!",
                "severity": severity,
            }
            self.assertRecordValues(entry, [expected])
            self.assertEqual(entry_url_from_exc, service._get_log_entry_url(entry))


class TestDBLoggingExceptionUserError(TestDBLoggingExceptionBase):
    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        # Override to avoid registering twice the same controller route.
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_user/"
        )

    def test_log_exception_user(self):
        self._test_exception(
            "user",
            log_exceptions.RESTServiceUserErrorException,
            "odoo.exceptions.UserError",
            "functional",
        )


class TestDBLoggingExceptionValidationError(TestDBLoggingExceptionBase):
    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_validation/"
        )

    def test_log_exception_validation(self):
        self._test_exception(
            "validation",
            log_exceptions.RESTServiceValidationErrorException,
            "odoo.exceptions.ValidationError",
            "functional",
        )


class TestDBLoggingExceptionValueError(TestDBLoggingExceptionBase):
    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_value/"
        )

    def test_log_exception_value(self):
        self._test_exception(
            "value", log_exceptions.RESTServiceDispatchException, "ValueError", "severe"
        )


class TestDBLoggingRetryableError(
    TransactionRestServiceRegistryCase, TestDBLoggingMixin
):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_registry(cls)

    @classmethod
    def tearDownClass(cls):
        # pylint: disable=W8110
        cls._teardown_registry(cls)
        super().tearDownClass()

    def _test_exception(self, test_type, wrapping_exc, exc_name, severity):
        log_model = self.env["rest.log"].sudo()
        initial_entries = log_model.search([])
        # Context: we are running in a transaction case which uses savepoints.
        # The log machinery is going to rollback the transation when catching errors.
        # Hence we need a completely separated env for the service.
        with new_rollbacked_env() as new_env:
            # Init fake collection w/ new env
            collection = _PseudoCollection(self._collection_name, new_env)
            service = self._get_service(self, collection=collection)
            with self._get_mocked_request(env=new_env):
                try:
                    service.dispatch("fail", test_type)
                except Exception as err:
                    # Not using `assertRaises` to inspect the exception directly
                    self.assertTrue(isinstance(err, wrapping_exc))
                    self.assertEqual(
                        service._get_exception_message(err), "Failed as you wanted!"
                    )

        with new_rollbacked_env() as new_env:
            log_model = new_env["rest.log"].sudo()
            entry = log_model.search([]) - initial_entries
            expected = {
                "collection": service._collection,
                "state": "failed",
                "result": "null",
                "exception_name": exc_name,
                "exception_message": "Failed as you wanted!",
                "severity": severity,
            }
            self.assertRecordValues(entry, [expected])

    @staticmethod
    def _get_test_controller(class_or_instance, root_path=None):
        return super()._get_test_controller(
            class_or_instance, root_path="/test_log_exception_retryable/"
        )

    def test_log_exception_retryable(self):
        # retryable error must bubble up to the retrying mechanism
        self._test_exception(
            "retryable",
            FakeConcurrentUpdateError,
            "odoo.addons.rest_log.tests.common.FakeConcurrentUpdateError",
            "warning",
        )
