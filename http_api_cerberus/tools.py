# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Convert Cerberus schemas to JSON schemas (OpenAPI flavor).

Heavily inspired by `cerberus_to_json` and its helpers in `base_rest.tools`
(OCA/rest-framework, ACSONE SA/NV): same mapping of rules,
plus support for `date` and multiple types.
"""

import logging

_logger = logging.getLogger(__name__)

# Cerberus type -> (JSON type, JSON format)
TYPE_MAP = {
    "boolean": ("boolean", None),
    "date": ("string", "date"),
    "datetime": ("string", "date-time"),
    "dict": ("object", None),
    "float": ("number", "float"),
    "integer": ("integer", None),
    "list": ("array", None),
    "number": ("number", None),
    "objectid": ("string", "objectid"),
    "string": ("string", None),
}
# Cerberus rule -> JSON keyword, for rules w/ the same value in both
SIMPLE_RULES = {
    "allowed": "enum",
    "default": "default",
    "description": "description",
    "nullable": "nullable",
    "readonly": "readOnly",
    "regex": "pattern",
}
SUPPORTED_META = ("title", "description", "example", "examples")
NUMERIC_TYPES = ("integer", "float", "number")


def cerberus_to_json(schema):
    """Convert a Cerberus schema (a dict of fields) to a JSON object schema."""
    return {
        "type": "object",
        # sorted to get stable docs
        "required": sorted(k for k, spec in schema.items() if spec.get("required")),
        "properties": {k: field_to_json(spec) for k, spec in schema.items()},
    }


def field_to_json(spec):
    """Convert the Cerberus rules of a field to a JSON schema."""
    _type = spec.get("type")
    if _type is None:
        return {}
    if isinstance(_type, list | tuple):
        return {"anyOf": [field_to_json(dict(spec, type=t)) for t in _type]}
    json_type, json_format = TYPE_MAP.get(_type, (_type, None))
    res = {"type": json_type}
    if json_format:
        res["format"] = json_format
    for rule, keyword in SIMPLE_RULES.items():
        if rule in spec:
            res[keyword] = spec[rule]
    for key in SUPPORTED_META:
        value = spec.get("meta", {}).get(key)
        if value:
            res[key] = value
    _add_bounds(_type, spec, res)
    if json_type == "object":
        _add_object_rules(spec, res)
    elif json_type == "array":
        res["items"] = field_to_json(spec["schema"]) if "schema" in spec else {}
        if not res["items"]:
            res["items"] = {"type": "string"}
    return res


def _add_bounds(_type, spec, res):
    """Map min/max rules: lengths for strings and lists, values for numbers."""
    length_keys = {
        "string": ("minLength", "maxLength"),
        "list": ("minItems", "maxItems"),
    }
    if _type in length_keys:
        min_key, max_key = length_keys[_type]
        if "minlength" in spec:
            res[min_key] = spec["minlength"]
        if "maxlength" in spec:
            res[max_key] = spec["maxlength"]
    if _type in NUMERIC_TYPES:
        if "min" in spec:
            res["minimum"] = spec["min"]
        if "max" in spec:
            res["maximum"] = spec["max"]


def _add_object_rules(spec, res):
    """Map nested schemas and `valuesrules` of dicts."""
    if "schema" in spec:
        res.update(cerberus_to_json(spec["schema"]))
    keys_type = spec.get("keysrules", {}).get("type", "string")
    if keys_type != "string":
        _logger.debug("JSON schema supports only string keys. Got: %s", keys_type)
    if "valuesrules" in spec:
        values_rules = spec["valuesrules"]
        additional = {"type": TYPE_MAP.get(values_rules.get("type"), ("string",))[0]}
        if "schema" in values_rules:
            additional.update(cerberus_to_json(values_rules["schema"]))
        res["additionalProperties"] = additional
