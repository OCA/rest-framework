# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo.tests.common import BaseCase

from ..tools import cerberus_to_json


class TestTools(BaseCase):
    def test_cerberus_to_json(self):
        """Each Cerberus rule maps to its JSON schema equivalent."""
        schema = {
            "name": {
                "type": "string",
                "required": True,
                "minlength": 1,
                "maxlength": 10,
                "meta": {"title": "Name", "example": "John"},
            },
            "kind": {"type": "string", "allowed": ["a", "b"], "default": "a"},
            "qty": {"type": "float", "min": 0, "max": 5, "nullable": True},
            "when": {"type": "datetime", "readonly": True},
            "day": {"type": "date"},
            "code": {"type": "string", "regex": "^[A-Z]+$"},
            "ids": {"type": "list", "schema": {"type": "integer"}, "minlength": 1},
            "tags": {"type": "list"},
            "child": {
                "type": "dict",
                "schema": {"id": {"type": "integer", "required": True}},
            },
            "mapping": {"type": "dict", "valuesrules": {"type": "integer"}},
            "any": {"type": ["string", "integer"]},
            "untyped": {"required": True},
        }
        self.assertEqual(
            cerberus_to_json(schema),
            {
                "type": "object",
                "required": ["name", "untyped"],
                "properties": {
                    "name": {
                        "type": "string",
                        "minLength": 1,
                        "maxLength": 10,
                        "title": "Name",
                        "example": "John",
                    },
                    "kind": {"type": "string", "enum": ["a", "b"], "default": "a"},
                    "qty": {
                        "type": "number",
                        "format": "float",
                        "minimum": 0,
                        "maximum": 5,
                        "nullable": True,
                    },
                    "when": {"type": "string", "format": "date-time", "readOnly": True},
                    "day": {"type": "string", "format": "date"},
                    "code": {"type": "string", "pattern": "^[A-Z]+$"},
                    "ids": {
                        "type": "array",
                        "minItems": 1,
                        "items": {"type": "integer"},
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "child": {
                        "type": "object",
                        "required": ["id"],
                        "properties": {"id": {"type": "integer"}},
                    },
                    "mapping": {
                        "type": "object",
                        "additionalProperties": {"type": "integer"},
                    },
                    "any": {"anyOf": [{"type": "string"}, {"type": "integer"}]},
                    "untyped": {},
                },
            },
        )
