# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from typing import List

import pydantic

from .. import models
from .common import PydanticRegistryCase, TransactionPydanticRegistryCase


class TestPydantic(PydanticRegistryCase):
    def test_simple_inheritance(self):
        class Location(models.BaseModel):
            _name = "location"
            lat = 0.1
            lng = 10.1

            def test(self) -> str:
                return "location"

        class ExtendedLocation(models.BaseModel):
            _inherit = "location"
            name: str

            def test(self, return_super: bool = False) -> str:
                if return_super:
                    return super(ExtendedLocation, self).test()
                return "extended"

        self._build_pydantic_classes(Location, ExtendedLocation)
        ClsLocation = self.pydantic_registry["location"]
        self.assertTrue(issubclass(ClsLocation, ExtendedLocation))
        self.assertTrue(issubclass(ClsLocation, Location))
        properties = ClsLocation.schema().get("properties", {}).keys()
        self.assertSetEqual({"lat", "lng", "name"}, set(properties))
        location = ClsLocation(name="name", lng=5.0, lat=4.2)
        self.assertDictEqual(location.dict(), {"lat": 4.2, "lng": 5.0, "name": "name"})
        self.assertEqual(location.test(), "extended")
        self.assertEqual(location.test(return_super=True), "location")

    def test_composite_inheritance(self):
        class Coordinate(models.BaseModel):
            _name = "coordinate"
            lat = 0.1
            lng = 10.1

        class Name(models.BaseModel):
            _name = "name"
            name: str

        class Location(models.BaseModel):
            _name = "location"
            _inherit = ["name", "coordinate"]

        self._build_pydantic_classes(Coordinate, Name, Location)
        self.assertIn("coordinate", self.pydantic_registry)
        self.assertIn("name", self.pydantic_registry)
        self.assertIn("location", self.pydantic_registry)
        ClsLocation = self.pydantic_registry["location"]
        self.assertTrue(issubclass(ClsLocation, Coordinate))
        self.assertTrue(issubclass(ClsLocation, Name))
        properties = ClsLocation.schema().get("properties", {}).keys()
        self.assertSetEqual({"lat", "lng", "name"}, set(properties))
        location = ClsLocation(name="name", lng=5.0, lat=4.2)
        self.assertDictEqual(location.dict(), {"lat": 4.2, "lng": 5.0, "name": "name"})

    def test_model_relation(self):
        class Person(models.BaseModel):
            _name = "person"
            name: str
            coordinate: "coordinate"

        class Coordinate(models.BaseModel):
            _name = "coordinate"
            lat = 0.1
            lng = 10.1

        self._build_pydantic_classes(Person, Coordinate)
        self.assertIn("coordinate", self.pydantic_registry)
        self.assertIn("person", self.pydantic_registry)
        ClsPerson = self.pydantic_registry["person"]
        ClsCoordinate = self.pydantic_registry["coordinate"]
        person = ClsPerson(name="test", coordinate={"lng": 5.0, "lat": 4.2})
        coordinate = person.coordinate
        self.assertTrue(isinstance(coordinate, Coordinate))
        # sub schema are stored into the definition property
        definitions = ClsPerson.schema().get("definitions", {})
        self.assertIn("coordinate", definitions)
        self.assertDictEqual(definitions["coordinate"], ClsCoordinate.schema())

    def test_inherit_bases(self):
        """ Check all BaseModels inherit from base """

        class Coordinate(models.BaseModel):
            _name = "coordinate"
            lat = 0.1
            lng = 10.1

        class Base(models.BaseModel):
            _inherit = "base"
            title: str = "My title"

        self._build_pydantic_classes(Coordinate, Base)
        self.assertIn("coordinate", self.pydantic_registry)
        self.assertIn("base", self.pydantic_registry)
        ClsCoordinate = self.pydantic_registry["coordinate"]
        self.assertTrue(issubclass(ClsCoordinate, models.Base))
        properties = ClsCoordinate.schema().get("properties", {}).keys()
        self.assertSetEqual({"lat", "lng", "title"}, set(properties))

    def test_from_orm(self):
        class User(models.BaseModel):
            _name = "user"
            _inherit = "odoo_orm_mode"
            name: str
            groups: List["group"] = pydantic.Field(alias="groups_id")  # noqa: F821

        class Group(models.BaseModel):
            _name = "group"
            _inherit = "odoo_orm_mode"
            name: str

        self._build_pydantic_classes(User, Group)
        ClsUser = self.pydantic_registry["user"]
        odoo_user = self.env.user
        user = ClsUser.from_orm(odoo_user)
        expected = {
            "name": odoo_user.name,
            "groups": [{"name": g.name} for g in odoo_user.groups_id],
        }
        self.assertDictEqual(user.dict(), expected)


class TestRegistryAccess(TransactionPydanticRegistryCase):
    def test_registry_access(self):
        """Check the access to the registry directly on Env"""
        base = self.env.pydantic_registry["base"]
        self.assertIsInstance(base(), models.BaseModel)
