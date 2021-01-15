# Copyright 2020 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from cerberus import Validator

from odoo.exceptions import UserError
from odoo.tests.common import MetaCase, TreeCase

from ..restapi import CerberusValidator


class TestCerberusValidator(TreeCase, MetaCase("DummyCase", (object,), {})):
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

    def test_to_openapi_responses(self):
        res = self.simple_schema_cerberus_validator.to_openapi_responses(None)
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
        res = self.nested_schema_cerberus_validator.to_openapi_responses(None)
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
        res = self.simple_schema_cerberus_validator.to_openapi_requestbody(None)
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
        res = self.nested_schema_cerberus_validator.to_openapi_requestbody(None)
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
        res = self.simple_schema_cerberus_validator.to_openapi_query_parameters(None)
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
        res = self.nested_schema_cerberus_validator.to_openapi_query_parameters(None)
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
            self.simple_schema_cerberus_validator.from_params(None, params={})

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
            self.simple_schema_cerberus_validator.to_response(None, result={})

    def test_schema_lookup_from_string(self):
        class MyService(object):
            def _get_simple_schema(self):
                return {"name": {"type": "string", "required": True, "nullable": True}}

        v = CerberusValidator(schema="_get_simple_schema")
        validator = v.get_cerberus_validator(MyService())
        self.assertTrue(validator)
        self.assertDictEqual(
            validator.root_schema.schema,
            {"name": {"type": "string", "required": True, "nullable": True}},
        )

    def test_schema_lookup_from_string_custom_validator(self):
        class MyService(object):
            def _get_simple_schema(self):
                return Validator(
                    {"name": {"type": "string", "required": False}}, require_all=True
                )

        v = CerberusValidator(schema="_get_simple_schema")
        validator = v.get_cerberus_validator(MyService())
        self.assertTrue(validator.require_all)
