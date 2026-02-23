# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import json

from odoo.exceptions import UserError

from odoo.addons.base_rest import restapi

from pydantic import BaseModel, ValidationError


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
            raise UserError(service.env._("BadRequest %s") % ve.json(indent=0)) from ve

    def to_response(self, service, result):
        # do we really need to validate the instance????
        json_dict = result.model_dump()
        orm_mode = result.model_config.get("from_attributes", None)
        to_validate = json_dict if orm_mode else result.model_dump(by_alias=True)
        # Ensure that to_validate is under json format
        try:
            json.loads(to_validate)
            to_validate_jsonified = to_validate
        except TypeError:
            to_validate_jsonified = json.dumps(to_validate)

        try:
            self._model_cls.model_validate_json(to_validate_jsonified)
        except ValidationError as validation_error:
            raise SystemError(service.env._("Invalid Response")) from validation_error
        return json_dict

    def to_openapi_query_parameters(self, servic, spec):
        json_schema = self._model_cls.model_json_schema()
        parameters = []
        for prop, spec in list(json_schema["properties"].items()):
            params = {
                "name": prop,
                "in": "query",
                "required": prop in json_schema.get("required", []),
                "allowEmptyValue": spec.get("nullable", False),
                "default": spec.get("default"),
                "schema": {},
            }
            if "anyOf" in spec:
                params["schema"]["anyOf"] = spec["anyOf"]
            elif "oneOf" in spec:
                params["schema"]["oneOf"] = spec["oneOf"]
            elif "type" in spec:
                params["schema"]["type"] = spec["type"]
            if spec.get("nullable", False):
                if "type" in params["schema"]:
                    params["schema"]["type"] = ["null", params["schema"]["type"]]
                elif "anyOf" in params["schema"]:
                    params["schema"]["anyOf"].append({"type": "null"})
                elif "oneOf" in params["schema"]:
                    params["schema"]["oneOf"].append({"type": "null"})

            if "enum" in spec:
                params["schema"]["enum"] = spec["enum"]

            parameters.append(params)

            if spec.get("type") == "array":
                # To correctly handle array into the url query string,
                # the name must ends with []
                params["name"] = params["name"] + "[]"

        return parameters

    # TODO, we should probably get the spec as parameters. That should
    # allows to add the definition of a schema only once into the specs
    # and use a reference to the schema into the parameters
    def to_openapi_requestbody(self, service, spec):
        return {
            "content": {
                "application/json": {
                    "schema": self.to_json_schema(service, spec, "input")
                }
            }
        }

    def to_openapi_responses(self, service, spec):
        return {
            "200": {
                "content": {
                    "application/json": {
                        "schema": self.to_json_schema(service, spec, "output")
                    }
                }
            }
        }

    def to_json_schema(self, service, spec, direction):
        schema = self._model_cls.model_json_schema(by_alias=False)
        schema_name = schema["title"]
        if schema_name not in spec.components.schemas:
            definitions = schema.pop("$defs", {})
            for name, sch in definitions.items():
                if name in spec.components.schemas:
                    continue
                sch = replace_ref_in_schema(sch, sch)
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
        self._do_validate(service, params, "input")
        return [
            super(PydanticModelList, self).from_params(service, param)
            for param in params
        ]

    def to_response(self, service, result):
        self._do_validate(service, result, "output")
        return [
            super(PydanticModelList, self).to_response(service=service, result=r)
            for r in result
        ]

    def to_openapi_query_parameters(self, service, spec):
        raise NotImplementedError("List are not (?yet?) supported as query paramters")

    def _do_validate(self, service, values, direction):
        ExceptionClass = UserError if direction == "input" else SystemError
        if self._min_items is not None and len(values) < self._min_items:
            raise ExceptionClass(
                service.env._(
                    (
                        "BadRequest: Not enough items in the list (%(current)s < "
                        "%(expected)s)"
                    ),
                    current=len(values),
                    expected=self._min_items,
                )
            )
        if self._max_items is not None and len(values) > self._max_items:
            raise ExceptionClass(
                service.env._(
                    (
                        "BadRequest: Too many items in the list (%(current)s > "
                        "%(expected)s)"
                    ),
                    current=len(values),
                    expected=self._max_items,
                )
            )

    # TODO, we should probably get the spec as parameters. That should
    # allows to add the definition of a schema only once into the specs
    # and use a reference to the schema into the parameters
    def to_openapi_requestbody(self, service, spec):
        return {
            "content": {
                "application/json": {
                    "schema": self.to_json_schema(service, spec, "input")
                }
            }
        }

    def to_openapi_responses(self, service, spec):
        return {
            "200": {
                "content": {
                    "application/json": {
                        "schema": self.to_json_schema(service, spec, "output")
                    }
                }
            }
        }

    def to_json_schema(self, service, spec, direction):
        json_schema = super().to_json_schema(service, spec, direction)
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
