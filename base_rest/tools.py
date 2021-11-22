# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from collections import OrderedDict


def cerberus_to_json(schema):
    """Convert a Cerberus schema to a JSON schema
    """
    result = OrderedDict()
    required = []
    properties = OrderedDict()
    result['type'] = 'object'
    result['required'] = required
    result['properties'] = properties
    for field, spec in schema.items():
        props = _get_field_props(spec)
        properties[field] = props
        if spec.get('required'):
            required.append(field)
    return result


def _get_field_props(spec):
    resp = OrderedDict()
    # dictionary of tuple (json type, json fromat) by cerberus type for
    # cerberus types requiring a specific mapping to a json type/format
    type_map = {
        'dict': ('object',),
        'list': ('array',),
        'objectid': ('string', 'objectid'),
        'datetime': ('string', 'date-time'),
        'float': ('number', 'float'),
    }
    _type = spec.get('type')
    if _type is None:
        return resp

    if 'description' in spec:
        resp['description'] = spec['description']

    if 'allowed' in spec:
        resp['enum'] = spec['allowed']

    if 'default' in spec:
        resp['default'] = spec['default']

    if 'minlength' in spec:
        if _type == 'string':
            resp['minLength'] = spec['minlength']
        elif _type == 'list':
            resp['minItems'] = spec['minlength']

    if 'maxlength' in spec:
        if _type == 'string':
            resp['maxLength'] = spec['maxlength']
        elif _type == 'list':
            resp['maxItems'] = spec['maxlength']

    if 'min' in spec:
        if _type in ['number', 'integer', 'float']:
            resp['minimum'] = spec['min']

    if 'max' in spec:
        if _type in ['number', 'integer', 'float']:
            resp['maximum'] = spec['max']

    if 'readonly' in spec:
        resp['readOnly'] = spec['readonly']

    if 'regex' in spec:
        resp['pattern'] = spec['regex']

    if 'nullable' in spec:
        resp['nullable'] = spec['nullable']

    json_type = type_map.get(_type, (_type,))

    resp['type'] = json_type[0]
    if json_type[0] == 'object':
        if 'schema' in spec:
            resp.update(cerberus_to_json(spec['schema']))
    elif json_type[0] == 'array':
        if 'schema' in spec:
            resp['items'] = _get_field_props(spec['schema'])
        else:
            resp['items'] = {'type': 'string'}
    else:
        try:
            resp['format'] = json_type[1]
        except IndexError:
            pass

    return resp
