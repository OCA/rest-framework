from odoo import models


class RESTModelMixin(models.AbstractModel):
    BASE_FIELD_TYPES = [
        'char', 'text', 'integer', 'float', 'date', 'datetime', 'boolean',
        'selection']
    _name = 'rest.mixin'

    _rest_fields_map = {}
    _rest_inverse_fields_map = {}

    def _setup_complete(self):
        res = super(RESTModelMixin, self)._setup_complete()
        cls = type(self)
        if not cls._rest_fields_map:
            self.build_default_rest_fields_map()
        self.build_inverse_fields_map()
        return res

    def build_default_rest_fields_map(self):
        cls = type(self)
        cls._rest_fields_map = {
            'id': 'id',
            'name': self._rec_name,
        }

    def build_inverse_fields_map(self):
        self.__class__._rest_inverse_fields_map = {
            jf: of for of, jf in self._rest_fields_map.items()
        }

    def serialize_field(self, field_name):
        field_type = self._fields[field_name].type
        if field_type in self.BASE_FIELD_TYPES:
            # Use false only for boolean fields, convert to None otherwise
            if self[field_name] is False:
                return False if field_type == 'boolean' else None
            return self[field_name]
        if field_type == 'many2one':
            return self[field_name].id if self[field_name] else None
        if field_type in ('one2many', 'many2many'):
            return self[field_name].ids

    def to_json_field_name(self, field_name):
        return self._rest_fields_map.get(field_name, field_name)

    def to_odoo_field_name(self, json_field_name):
        return self._rest_inverse_fields_map.get(
            json_field_name, json_field_name)

    def to_json(self):
        return {
            self.to_json_field_name(f): self.serialize_field(f)
            for f in self._rest_fields_map
        }

    def from_json(self, data):
        return {
            self.to_odoo_field_name(k): v for k, v in data.items()
        }