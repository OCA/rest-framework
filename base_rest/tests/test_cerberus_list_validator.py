# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import unittest

from cerberus import Validator

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase

from ..components.cerberus_validator import BaseRestCerberusValidator
from ..restapi import CerberusListValidator


class TestCerberusListValidator(TransactionCase):
    """Test all the methods that must be implemented by CerberusListValidator to
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
        }
        cls.simple_schema_list_validator = CerberusListValidator(
            schema=cls.simple_schema, min_items=1, max_items=2, unique_items=True
        )
        cls.nested_schema_list_validator = CerberusListValidator(
            schema=cls.nested_schema
        )
        cls.maxDiff = None
        cls.mock_service = unittest.mock.Mock()
        cls.mock_service.env = cls.env

    def filter(self, record):
        # required to mute logger
        return 0

    def test_to_openapi_responses(self):
        res = self.simple_schema_list_validator.to_openapi_responses(None, None)
        self.assertDictEqual(
            res,
            {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "items": {
                                    "type": "object",
                                    "required": ["name"],
                                    "properties": {
                                        "name": {"nullable": True, "type": "string"},
                                        "title": {
                                            "enum": ["mr", "mm"],
                                            "nullable": False,
                                            "type": "string",
                                        },
                                    },
                                },
                                "maxItems": 2,
                                "minItems": 1,
                                "type": "array",
                                "uniqueItems": True,
                            }
                        }
                    }
                }
            },
        )
        res = self.nested_schema_list_validator.to_openapi_responses(None, None)
        self.assertDictEqual(
            res,
            {
                "200": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "items": {
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
                                    },
                                },
                                "type": "array",
                            }
                        }
                    }
                }
            },
        )

    def test_to_openapi_requestbody(self):
        res = self.simple_schema_list_validator.to_openapi_requestbody(None, None)
        self.assertEqual(
            res,
            {
                "content": {
                    "application/json": {
                        "schema": {
                            "items": {
                                "type": "object",
                                "required": ["name"],
                                "properties": {
                                    "name": {"nullable": True, "type": "string"},
                                    "title": {
                                        "enum": ["mr", "mm"],
                                        "nullable": False,
                                        "type": "string",
                                    },
                                },
                            },
                            "maxItems": 2,
                            "minItems": 1,
                            "type": "array",
                            "uniqueItems": True,
                        }
                    }
                }
            },
        )
        res = self.nested_schema_list_validator.to_openapi_requestbody(None, None)
        self.assertDictEqual(
            res,
            {
                "content": {
                    "application/json": {
                        "schema": {
                            "items": {
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
                                },
                            },
                            "type": "array",
                        }
                    }
                }
            },
        )

    def test_to_openapi_query_parameters(self):
        with self.assertRaises(NotImplementedError):
            self.simple_schema_list_validator.to_openapi_query_parameters(None, None)

    def test_from_params_ignore_unknown(self):
        params = [{"name": "test", "unknown": True}]
        res = self.simple_schema_list_validator.from_params(None, params=params)
        self.assertListEqual(res, [{"name": "test"}])

    def test_from_params_validation(self):
        # minItems / maxItems
        with self.assertRaises(UserError):
            # minItems = 1
            self.simple_schema_list_validator.from_params(self.mock_service, params=[])
        with self.assertRaises(UserError):
            # maxItems = 2
            self.simple_schema_list_validator.from_params(
                self.mock_service,
                params=[{"name": "test"}, {"name": "test"}, {"name": "test"}],
            )
        with self.assertRaises(UserError):
            # name required
            self.simple_schema_list_validator.from_params(
                self.mock_service, params=[{}]
            )

    def test_to_response_ignore_unknown(self):
        result = [{"name": "test", "unknown": True}]
        res = self.simple_schema_list_validator.to_response(None, result=result)
        self.assertListEqual(res, [{"name": "test"}])

    def test_to_response_validation(self):
        # If a response is not conform to the expected schema it's considered
        # as a programmatic error not a user error
        with self.assertRaises(SystemError):
            # minItems = 1
            self.simple_schema_list_validator.to_response(self.mock_service, result=[])
        with self.assertRaises(SystemError):
            # maxItems = 2
            self.simple_schema_list_validator.to_response(
                self.mock_service,
                result=[{"name": "test"}, {"name": "test"}, {"name": "test"}],
            )
        with self.assertRaises(SystemError):
            # name required
            self.simple_schema_list_validator.to_response(
                self.mock_service, result=[{}]
            )

    def test_schema_lookup_from_string(self):
        class MyService:
            def _get_simple_schema(self):
                return {"name": {"type": "string", "required": True, "nullable": True}}

            def component(self, *args, **kwargs):
                return BaseRestCerberusValidator(unittest.mock.Mock())

        v = CerberusListValidator(schema="_get_simple_schema")
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

        v = CerberusListValidator(schema="_get_simple_schema")
        validator = v.get_cerberus_validator(MyService(), "input")
        self.assertTrue(validator.require_all)
