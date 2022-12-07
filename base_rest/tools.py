# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import inspect
import logging
from collections import OrderedDict

_logger = logging.getLogger(__name__)

# Decorator attribute added on a route function (cfr Odoo's route)
ROUTING_DECORATOR_ATTR = "original_routing"
SUPPORTED_META = ["title", "description", "example", "examples"]


def cerberus_to_json(schema):
    """Convert a Cerberus schema to a JSON schema"""
    result = OrderedDict()
    required = []
    properties = OrderedDict()
    result["type"] = "object"
    result["required"] = required
    result["properties"] = properties
    for field, spec in list(schema.items()):
        props = _get_field_props(spec)
        properties[field] = props
        if spec.get("required"):
            required.append(field)
    # sort required to get the same order on each run and easy comparison into
    # the tests
    required.sort()
    return result


def _get_field_props(spec):  # noqa: C901
    resp = OrderedDict()
    # dictionary of tuple (json type, json fromat) by cerberus type for
    # cerberus types requiring a specific mapping to a json type/format
    type_map = {
        "dict": ("object",),
        "list": ("array",),
        "objectid": ("string", "objectid"),
        "datetime": ("string", "date-time"),
        "float": ("number", "float"),
    }
    _type = spec.get("type")
    if _type is None:
        return resp

    if "description" in spec:
        resp["description"] = spec["description"]

    if "meta" in spec:
        for key in SUPPORTED_META:
            value = spec["meta"].get(key)
            if value:
                resp[key] = value
    if "allowed" in spec:
        resp["enum"] = spec["allowed"]

    if "default" in spec:
        resp["default"] = spec["default"]

    if "minlength" in spec:
        if _type == "string":
            resp["minLength"] = spec["minlength"]
        elif _type == "list":
            resp["minItems"] = spec["minlength"]

    if "maxlength" in spec:
        if _type == "string":
            resp["maxLength"] = spec["maxlength"]
        elif _type == "list":
            resp["maxItems"] = spec["maxlength"]

    if "min" in spec:
        if _type in ["number", "integer", "float"]:
            resp["minimum"] = spec["min"]

    if "max" in spec:
        if _type in ["number", "integer", "float"]:
            resp["maximum"] = spec["max"]

    if "readonly" in spec:
        resp["readOnly"] = spec["readonly"]

    if "regex" in spec:
        resp["pattern"] = spec["regex"]

    if "nullable" in spec:
        resp["nullable"] = spec["nullable"]

    if "allowed" in spec:
        resp["enum"] = spec["allowed"]

    json_type = type_map.get(_type, (_type,))

    resp["type"] = json_type[0]
    if json_type[0] == "object":
        if "schema" in spec:
            resp.update(cerberus_to_json(spec["schema"]))
        additional_properties = {}
        if "keysrules" in spec:
            rule_value_type = spec["keysrules"].get("type", "string")
            if rule_value_type != "string":
                _logger.debug(
                    "Openapi only support key/value mapping definition where"
                    " the keys are strings. Received %s",
                    rule_value_type,
                )
        if "valuesrules" in spec:
            values_rules = spec["valuesrules"]
            rule_value_type = values_rules.get("type", "string")
            additional_properties["type"] = rule_value_type
            if "schema" in values_rules:
                additional_properties.update(cerberus_to_json(values_rules["schema"]))
        if additional_properties:
            resp["additionalProperties"] = additional_properties
    elif json_type[0] == "array":
        if "schema" in spec:
            resp["items"] = _get_field_props(spec["schema"])
        else:
            resp["items"] = {"type": "string"}
    else:
        try:
            resp["format"] = json_type[1]
        # pylint:disable=except-pass
        except IndexError:
            pass

    return resp


def _inspect_methods(cls):
    """Return all methods of a given class as (name, value) pairs sorted by
    name.
    inspect.getmembers was initially used. Unfortunately, instance's properties
    was accessed into the loop and could raise some exception since we are
    into the startup process and all the resources are not yet initialized.
    """
    results = []
    for attribute in inspect.classify_class_attrs(cls):
        if attribute.kind != "method":
            continue
        name = attribute.name
        method = getattr(cls, name)
        results.append((name, method))
    results.sort(key=lambda pair: pair[0])
    return results
