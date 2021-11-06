# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import marshmallow
from apispec.ext.marshmallow.openapi import OpenAPIConverter
from marshmallow.exceptions import ValidationError

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.base_rest import restapi


class Datamodel(restapi.RestMethodParam):
    def __init__(self, name, is_list=False, partial=None):
        """

        :param name: The datamodel name
        :param is_list: Should be set to True if params is a collection so that
                        the object will be de/serialized from/to a list
        :param partial: Whether to ignore missing fields and not require
            any fields declared. Propagates down to ``Nested`` fields as well. If
            its value is an iterable, only missing fields listed in that iterable
            will be ignored. Use dot delimiters to specify nested fields.
        """
        self._name = name
        self._is_list = is_list
        self._partial = partial

    def from_params(self, service, params):
        ModelClass = service.env.datamodels[self._name]
        try:
            return ModelClass.load(
                params,
                many=self._is_list,
                unknown=marshmallow.EXCLUDE,
                partial=self._partial,
            )
        except ValidationError as ve:
            raise UserError(_("BadRequest %s") % ve.messages)

    def to_response(self, service, result):
        ModelClass = service.env.datamodels[self._name]
        if self._is_list:
            json = [i.dump() for i in result]
        else:
            json = result.dump()
        errors = ModelClass.validate(
            json, many=self._is_list, unknown=marshmallow.EXCLUDE
        )
        if errors:
            raise SystemError(_("Invalid Response %s") % errors)
        return json

    def to_openapi_query_parameters(self, service, spec):
        converter = self._get_converter()
        schema = self._get_schema(service)
        return converter.schema2parameters(schema, location="query")

    # TODO, we should probably get the spec as parameters. That should
    # allows to add the definition of a schema only once into the specs
    # and use a reference to the schema into the parameters
    def to_openapi_requestbody(self, service, spec):
        return {
            "content": {
                "application/json": {"schema": self.to_json_schema(service, "input")}
            }
        }

    def to_openapi_responses(self, service, spec):
        return {
            "200": {
                "content": {
                    "application/json": {
                        "schema": self.to_json_schema(service, "output")
                    }
                }
            }
        }

    def to_json_schema(self, service, direction):
        converter = self._get_converter()
        schema = self._get_schema(service)
        return converter.resolve_nested_schema(schema)

    def _get_schema(self, service):
        return service.env.datamodels[self._name].get_schema(many=self._is_list)

    def _get_converter(self):
        return OpenAPIConverter("3.0", self._schema_name_resolver, None)

    def _schema_name_resolver(self, schema):
        # name resolver used by the OpenapiConverter. always return None
        # to force nested schema definition
        return None


restapi.Datamodel = Datamodel
