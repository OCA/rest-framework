# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import unittest

from cerberus import Validator

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from ..components.cerberus_validator import BaseRestCerberusValidator
from ..restapi import CerberusValidator
from ..tools import cerberus_to_json


class TestCerberusValidator(TransactionCase):
    """Test all the methods that must be implemented by CerberusValidator to
    be a valid RestMethodParam"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.simple_schema = {
            "name": {"type": "string", "required": True, "nullable": True},
            "title": {
                "type": "string",
                "nullable": False,
                "required": False,
                "allowed": ["mr", "mm"],
            },
            "age": {"type": "integer", "default": 18},
            "interests": {"type": "list", "schema": {"type": "string"}},
        }

        cls.nested_schema = {
            "name": {"type": "string", "required": True, "empty": False},
            "country": {
                "type": "dict",
                "schema": {
                    "id": {"type": "integer", "required": True, "nullable": False},
                    "name": {"type": "string"},
                },
            },
            "is_company": {"type": "boolean"},
        }
        cls.simple_schema_cerberus_validator = CerberusValidator(
            schema=cls.simple_schema
        )
        cls.nested_schema_cerberus_validator = CerberusValidator(
            schema=cls.nested_schema
        )
        cls.mock_service = unittest.mock.Mock()
        cls.mock_service.env = cls.env

    def test_to_openapi_responses(self):
        res = self.simple_schema_cerberus_validator.to_openapi_responses(None, None)
        self.assertDictEqual(
            res,
            {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"nullable": True, "type": "string"},
                                    "title": {
                                        "enum": ["mr", "mm"],
                                        "nullable": False,
                                        "type": "string",
                                    },
                                    "age": {"default": 18, "type": "integer"},
                                    "interests": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                },
                            }
                        }
                    }
                }
            },
        )
        res = self.nested_schema_cerberus_validator.to_openapi_responses(None, None)
        self.assertDictEqual(
            res,
            {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "country": {
                                        "type": "object",
                                        "required": ["id"],
                                        "properties": {
                                            "id": {
                                                "nullable": False,
                                                "type": "integer",
                                            },
                                            "name": {"type": "string"},
                                        },
                                    },
                                    "is_company": {"type": "boolean"},
                                },
                            }
                        }
                    }
                }
            },
        )

    def test_to_openapi_requestbody(self):
        res = self.simple_schema_cerberus_validator.to_openapi_requestbody(None, None)
        self.assertEqual(
            res,
            {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"nullable": True, "type": "string"},
                                "title": {
                                    "enum": ["mr", "mm"],
                                    "nullable": False,
                                    "type": "string",
                                },
                                "age": {"default": 18, "type": "integer"},
                                "interests": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                },
                            },
                        }
                    }
                }
            },
        )
        res = self.nested_schema_cerberus_validator.to_openapi_requestbody(None, None)
        self.assertDictEqual(
            res,
            {
                "content": {
                    "application/json": {
                        "schema": {
                            "type": "object",
                            "required": ["name"],
                            "properties": {
                                "name": {"type": "string"},
                                "country": {
                                    "type": "object",
                                    "required": ["id"],
                                    "properties": {
                                        "id": {"nullable": False, "type": "integer"},
                                        "name": {"type": "string"},
                                    },
                                },
                                "is_company": {"type": "boolean"},
                            },
                        }
                    }
                }
            },
        )

    def test_to_openapi_query_parameters(self):
        res = self.simple_schema_cerberus_validator.to_openapi_query_parameters(
            None, None
        )
        self.assertListEqual(
            res,
            [
                {
                    "name": "name",
                    "in": "query",
                    "required": True,
                    "allowEmptyValue": True,
                    "default": None,
                    "schema": {"type": "string"},
                },
                {
                    "name": "title",
                    "in": "query",
                    "required": False,
                    "allowEmptyValue": False,
                    "default": None,
                    "schema": {"type": "string", "enum": ["mr", "mm"]},
                },
                {
                    "name": "age",
                    "in": "query",
                    "required": False,
                    "allowEmptyValue": False,
                    "default": 18,
                    "schema": {"type": "integer"},
                },
                {
                    "name": "interests[]",
                    "in": "query",
                    "required": False,
                    "allowEmptyValue": False,
                    "default": None,
                    "schema": {"type": "array", "items": {"type": "string"}},
                },
            ],
        )
        res = self.nested_schema_cerberus_validator.to_openapi_query_parameters(
            None, None
        )
        self.assertListEqual(
            res,
            [
                {
                    "name": "name",
                    "in": "query",
                    "required": True,
                    "allowEmptyValue": False,
                    "default": None,
                    "schema": {"type": "string"},
                },
                {
                    "name": "country",
                    "in": "query",
                    "required": False,
                    "allowEmptyValue": False,
                    "default": None,
                    "schema": {"type": "object"},
                },
                {
                    "name": "is_company",
                    "in": "query",
                    "required": False,
                    "allowEmptyValue": False,
                    "default": None,
                    "schema": {"type": "boolean"},
                },
            ],
        )

    def test_from_params_add_default(self):
        params = {"name": "test"}
        res = self.simple_schema_cerberus_validator.from_params(None, params=params)
        self.assertDictEqual(res, {"name": "test", "age": 18})

    def test_from_params_ignore_unknown(self):
        params = {"name": "test", "unknown": True}
        res = self.simple_schema_cerberus_validator.from_params(None, params=params)
        self.assertDictEqual(res, {"name": "test", "age": 18})

    def test_from_params_validation(self):
        # name is required
        with self.assertRaises(UserError):
            self.simple_schema_cerberus_validator.from_params(
                self.mock_service, params={}
            )

    def test_to_response_add_default(self):
        result = {"name": "test"}
        res = self.simple_schema_cerberus_validator.to_response(None, result=result)
        self.assertDictEqual(res, {"name": "test", "age": 18})

    def test_to_response_ignore_unknown(self):
        result = {"name": "test", "unknown": True}
        res = self.simple_schema_cerberus_validator.to_response(None, result=result)
        self.assertDictEqual(res, {"name": "test", "age": 18})

    def test_to_response_validation(self):
        # name is required
        # If a response is not conform to the expected schema it's considered
        # as a programmatic error not a user error
        with self.assertRaises(SystemError):
            self.simple_schema_cerberus_validator.to_response(
                self.mock_service, result={}
            )

    def test_schema_lookup_from_string(self):
        class MyService:
            def _get_simple_schema(self):
                return {"name": {"type": "string", "required": True, "nullable": True}}

            def component(self, *args, **kwargs):
                return BaseRestCerberusValidator(unittest.mock.Mock())

        v = CerberusValidator(schema="_get_simple_schema")
        validator = v.get_cerberus_validator(MyService(), "output")
        self.assertTrue(validator)
        self.assertDictEqual(
            validator.root_schema.schema,
            {"name": {"type": "string", "required": True, "nullable": True}},
        )

    def test_schema_lookup_from_string_custom_validator(self):
        class MyService:
            def _get_simple_schema(self):
                return Validator(
                    {"name": {"type": "string", "required": False}}, require_all=True
                )

            def component(self, *args, **kwargs):
                return BaseRestCerberusValidator(unittest.mock.Mock())

        v = CerberusValidator(schema="_get_simple_schema")
        validator = v.get_cerberus_validator(MyService(), "input")
        self.assertTrue(validator.require_all)

    def test_custom_validator_handler(self):
        assertEq = self.assertEqual

        class CustomBaseRestCerberusValidator(BaseRestCerberusValidator):
            def get_validator_handler(self, service, method_name, direction):
                # In your implementation, this is where you can handle how the
                # validator is retrieved / computed (dispatch to dedicated
                # components...).
                assertEq(service, my_service)
                assertEq(method_name, "my_endpoint")
                assertEq(direction, "input")
                # A callable with no parameter is expected.
                return lambda: Validator(
                    {"name": {"type": "string", "required": False}}, require_all=True
                )

            def has_validator_handler(self, service, method_name, direction):
                return True

        class MyService:
            def component(self, *args, **kwargs):
                return CustomBaseRestCerberusValidator(unittest.mock.Mock())

        my_service = MyService()

        v = CerberusValidator(schema="my_endpoint")
        validator = v.get_cerberus_validator(my_service, "input")
        self.assertTrue(validator.require_all)

    def test_cerberus_key_value_mapping_to_openapi(self):
        schema = {
            "indexes": {
                "type": "dict",
                "required": True,
                "nullable": True,
                "keysrules": {"type": "string"},
                "valuesrules": {"type": "string"},
            }
        }
        openapi = cerberus_to_json(schema)
        self.assertDictEqual(
            openapi,
            {
                "type": "object",
                "required": ["indexes"],
                "properties": {
                    "indexes": {
                        "nullable": True,
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    }
                },
            },
        )
        schema = {
            "indexes": {
                "type": "dict",
                "required": True,
                "nullable": True,
                "keysrules": {"type": "string"},
                "valuesrules": {
                    "type": "dict",
                    "schema": {
                        "id": {
                            "type": "integer",
                            "required": True,
                            "nullable": False,
                        },
                        "name": {"type": "string"},
                    },
                },
            }
        }
        openapi = cerberus_to_json(schema)
        self.assertDictEqual(
            openapi,
            {
                "type": "object",
                "required": ["indexes"],
                "properties": {
                    "indexes": {
                        "nullable": True,
                        "type": "object",
                        "additionalProperties": {
                            "type": "object",
                            "required": ["id"],
                            "properties": {
                                "id": {
                                    "nullable": False,
                                    "type": "integer",
                                },
                                "name": {"type": "string"},
                            },
                        },
                    }
                },
            },
        )

    def test_cerberus_meta_to_openapi(self):
        schema = {
            "indexes": {
                "type": "dict",
                "meta": {
                    "description": "A key/value mapping where Key is the model "
                    "name used to fill the index and value is the "
                    "index name",
                    "example": {
                        "shopinvader.category": "demo_elasticsearch_backend_"
                        "shopinvader_category_en_US",
                        "shopinvader.variant": "demo_elasticsearch_backend_"
                        "shopinvader_variant_en_US",
                    },
                },
                "required": True,
                "nullable": True,
                "keysrules": {"type": "string"},
                "valuesrules": {"type": "string"},
            }
        }
        openapi = cerberus_to_json(schema)
        self.assertDictEqual(
            openapi,
            {
                "type": "object",
                "required": ["indexes"],
                "properties": {
                    "indexes": {
                        "description": "A key/value mapping where Key is the model "
                        "name used to fill the index and value is "
                        "the index name",
                        "example": {
                            "shopinvader.category": "demo_elasticsearch_backend_"
                            "shopinvader_category_en_US",
                            "shopinvader.variant": "demo_elasticsearch_backend_"
                            "shopinvader_variant_en_US",
                        },
                        "nullable": True,
                        "type": "object",
                        "additionalProperties": {"type": "string"},
                    }
                },
            },
        )
