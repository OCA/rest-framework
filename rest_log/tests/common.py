# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import contextlib

from odoo import exceptions

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import Component, WorkContext

from .tools import MockRequest


class TestDBLoggingMixin(object):
    _collection_name = "base.rest.test"

    @staticmethod
    def _get_service(class_or_instance):
        # pylint: disable=R7980
        class LoggedService(Component):
            _inherit = "base.rest.service"
            _name = "test.log.service"
            _usage = "logmycalls"
            _collection = class_or_instance._collection_name
            _description = "Test log my calls"
            _log_calls_in_db = True

            def get(self, _id):
                """Get some information"""
                return {"name": "Mr Logger"}

            def fail(self, how):
                """Test a failure"""
                exc = {
                    "value": ValueError,
                    "validation": exceptions.ValidationError,
                    "user": exceptions.UserError,
                }
                raise exc[how]("Failed as you wanted!")

            def _validator_fail(self):
                return {"how": {"type": "string", "required": True}}

        class_or_instance._components_registry.load_components("rest_log")
        # class_or_instance._build_services(class_or_instance, LoggedService)
        # TODO: WTH _build_services does not load the component?
        LoggedService._build_component(class_or_instance._components_registry)
        return class_or_instance._get_service_component(class_or_instance, "logmycalls")

    @staticmethod
    def _get_service_component(class_or_instance, usage):
        collection = _PseudoCollection(
            class_or_instance._collection_name, class_or_instance.env
        )
        work = WorkContext(
            model_name="rest.service.registration",
            collection=collection,
            components_registry=class_or_instance._components_registry,
        )
        return work.component(usage=usage)

    @contextlib.contextmanager
    def _get_mocked_request(self, httprequest=None, extra_headers=None):
        with MockRequest(self.env) as mocked_request:
            mocked_request.httprequest = httprequest or mocked_request.httprequest
            headers = {"Cookie": "IaMaCookie!", "Api-Key": "I_MUST_STAY_SECRET"}
            headers.update(extra_headers or {})
            mocked_request.httprequest.headers = headers
            yield mocked_request

    def assertRecordValues(self, records, expected_values):  # noqa: C901
        for record, expected_value in zip(records, expected_values):
            for k, v in expected_value.items():
                self.assertEqual(record[k], v)
