# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import contextlib

from psycopg2 import errorcodes
from psycopg2.errors import OperationalError

from odoo import exceptions

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.website.tools import MockRequest


class TestDBLoggingMixin:
    @staticmethod
    def _get_service(class_or_instance, collection=None):
        # pylint: disable=R7980
        class LoggedService(Component):
            _inherit = "base.rest.service"
            _name = "test.log.service"
            _usage = "logmycalls"
            _collection = class_or_instance._collection_name
            _description = "Test log my calls"
            _log_calls_in_db = True

            @restapi.method(
                [(["/<int:id>/get", "/<int:id>"], "GET")],
                output_param=restapi.CerberusValidator("_get_out_schema"),
                auth="public",
            )
            def get(self, _id):
                """Get some information"""
                return {"name": "Mr Logger"}

            def _get_out_schema(self):
                return {"name": {"type": "string", "required": True}}

            @restapi.method([(["/fail/<string:how>"], "GET")], auth="public")
            def fail(self, how):
                """Test a failure"""
                exc = {
                    "value": ValueError,
                    "validation": exceptions.ValidationError,
                    "user": exceptions.UserError,
                    "retryable": FakeConcurrentUpdateError,
                }
                raise exc[how]("Failed as you wanted!")

        class_or_instance.comp_registry.load_components("rest_log")
        # class_or_instance._build_services(class_or_instance, LoggedService)
        # TODO: WTH _build_services does not load the component?
        LoggedService._build_component(class_or_instance.comp_registry)
        return class_or_instance._get_service_component(
            class_or_instance, "logmycalls", collection=collection
        )

    @contextlib.contextmanager
    def _get_mocked_request(self, env=None, httprequest=None, extra_headers=None):
        with MockRequest(env or self.env) as mocked_request:
            mocked_request.httprequest = httprequest or mocked_request.httprequest
            headers = {"Cookie": "IaMaCookie!", "Api-Key": "I_MUST_STAY_SECRET"}
            headers.update(extra_headers or {})
            mocked_request.httprequest.headers = headers
            yield mocked_request


class FakeConcurrentUpdateError(OperationalError):
    @property
    def pgcode(self):
        return errorcodes.SERIALIZATION_FAILURE
