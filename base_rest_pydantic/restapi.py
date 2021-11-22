# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.base_rest import restapi
from odoo.addons.pydantic.models import BaseModel

from pydantic import ValidationError, validate_model


def replace_ref_in_schema(item, original_schema):
    if isinstance(item, list):
        return [replace_ref_in_schema(i, original_schema) for i in item]
    elif isinstance(item, dict):
        if list(item.keys()) == ["$ref"]:
            schema = item["$ref"].split("/")[-1]
            return {"$ref": f"#/components/schemas/{schema}"}
        else:
            return {
                key: replace_ref_in_schema(i, original_schema)
                for key, i in item.items()
            }
    else:
        return item


class PydanticModel(restapi.RestMethodParam):
    def __init__(self, cls: BaseModel):
        """
        :param name: The pydantic model name
        """
        if not issubclass(cls, BaseModel):
            raise TypeError(
                f"{cls} is not a subclass of odoo.addons.pydantic.models.BaseModel"
            )
        self._model_cls = cls

    def from_params(self, service, params):
        try:
            return self._model_cls(**params)
        except ValidationError as ve:
            raise UserError(_("BadRequest %s") % ve.json(indent=0))

    def to_response(self, service, result):
        # do we really need to validate the instance????
        json_dict = result.dict()
        to_validate = (
            json_dict if not result.__config__.orm_mode else result.dict(by_alias=True)
        )
        *_, validation_error = validate_model(self._model_cls, to_validate)
        if validation_error:
            raise SystemError(_("Invalid Response %s") % validation_error)
        return json_dict

    def to_openapi_query_parameters(self, servic, spec):
        json_schema = self._model_cls.schema()
        parameters = []
        for prop, spec in list(json_schema["properties"].items()):
            params = {
                "name": prop,
                "in": "query",
                "required": prop in json_schema.get("required", []),
                "allowEmptyValue": spec.get("nullable", False),
                "default": spec.get("default"),
            }
            if spec.get("schema"):
                params["schema"] = spec.get("schema")
            else:
                params["schema"] = {"type": spec["type"]}
            if spec.get("items"):
                params["schema"]["items"] = spec.get("items")
            if "enum" in spec:
                params["schema"]["enum"] = spec["enum"]

            parameters.append(params)

            if spec["type"] == "array":
                # To correctly handle array into the url query string,
                # the name must ends with []
                params["name"] = params["name"] + "[]"

        return parameters

    # TODO, we should probably get the spec as parameters. That should
    # allows to add the definition of a schema only once into the specs
    # and use a reference to the schema into the parameters
    def to_openapi_requestbody(self, service, spec):
        return {"content": {"application/json": {"schema": self.to_json_schema(spec)}}}

    def to_openapi_responses(self, service, spec):
        return {
            "200": {
                "content": {"application/json": {"schema": self.to_json_schema(spec)}}
            }
        }

    def to_json_schema(self, spec):
        schema = self._model_cls.schema()
        schema_name = schema["title"]
        if schema_name not in spec.components.schemas:
            definitions = schema.get("definitions", {})
            for name, sch in definitions.items():
                if name in spec.components.schemas:
                    continue
                spec.components.schema(name, sch)
            schema = replace_ref_in_schema(schema, schema)
            spec.components.schema(schema_name, schema)
        return {"$ref": f"#/components/schemas/{schema_name}"}


class PydanticModelList(PydanticModel):
    def __init__(
        self,
        cls: BaseModel,
        min_items: int = None,
        max_items: int = None,
        unique_items: bool = None,
    ):
        """
        :param name: The pydantic model name
        :param min_items: A list instance is valid against "min_items" if its
                          size is greater than, or equal to, min_items.
                          The value MUST be a non-negative integer.
        :param max_items: A list instance is valid against "max_items" if its
                          size is less than, or equal to, max_items.
                          The value MUST be a non-negative integer.
        :param unique_items: Used to document that the list should only
                             contain unique items.
                             (Not enforced at validation time)
        """
        super().__init__(cls=cls)
        self._min_items = min_items
        self._max_items = max_items
        self._unique_items = unique_items

    def from_params(self, service, params):
        self._do_validate(params, "input")
        return [super(PydanticModelList, self).from_params(param) for param in params]

    def to_response(self, service, result):
        self._do_validate(result, "output")
        return [
            super(PydanticModelList, self).to_response(service=service, result=r)
            for r in result
        ]

    def to_openapi_query_parameters(self, service, spec):
        raise NotImplementedError("List are not (?yet?) supported as query paramters")

    def _do_validate(self, values, direction):
        ExceptionClass = UserError if direction == "input" else SystemError
        if self._min_items is not None and len(values) < self._min_items:
            raise ExceptionClass(
                _(
                    "BadRequest: Not enough items in the list (%s < %s)"
                    % (len(values), self._min_items)
                )
            )
        if self._max_items is not None and len(values) > self._max_items:
            raise ExceptionClass(
                _(
                    "BadRequest: Too many items in the list (%s > %s)"
                    % (len(values), self._max_items)
                )
            )

    # TODO, we should probably get the spec as parameters. That should
    # allows to add the definition of a schema only once into the specs
    # and use a reference to the schema into the parameters
    def to_openapi_requestbody(self, service, spec):
        return {"content": {"application/json": {"schema": self.to_json_schema(spec)}}}

    def to_openapi_responses(self, service, spec):
        return {
            "200": {
                "content": {"application/json": {"schema": self.to_json_schema(spec)}}
            }
        }

    def to_json_schema(self, spec):
        json_schema = super().to_json_schema(spec)
        json_schema = {"type": "array", "items": json_schema}
        if self._min_items is not None:
            json_schema["minItems"] = self._min_items
        if self._max_items is not None:
            json_schema["maxItems"] = self._max_items
        if self._unique_items is not None:
            json_schema["uniqueItems"] = self._unique_items
        return json_schema


restapi.PydanticModel = PydanticModel
restapi.PydanticModelList = PydanticModelList
