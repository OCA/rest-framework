# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from typing import List

try:
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

import pydantic

from .. import models, utils
from .common import PydanticRegistryCase


class TestPydantic(PydanticRegistryCase):
    def test_simple_inheritance(self):
        class Location(models.BaseModel):
            lat = 0.1
            lng = 10.1

            def test(self) -> str:
                return "location"

        class ExtendedLocation(Location, extends=Location):
            name: str

            def test(self, return_super: bool = False) -> str:
                if return_super:
                    return super(ExtendedLocation, self).test()
                return "extended"

        self._build_pydantic_classes(Location, ExtendedLocation)
        ClsLocation = self.pydantic_registry[Location.__xreg_name__]
        self.assertTrue(issubclass(ClsLocation, ExtendedLocation))
        self.assertTrue(issubclass(ClsLocation, Location))

        # check that the behaviour is the same for all the definitions
        # of the same model...
        classes = Location, ExtendedLocation, ClsLocation
        for cls in classes:
            schema = cls.schema()
            properties = schema.get("properties", {}).keys()
            self.assertEqual(schema.get("title"), "Location")
            self.assertSetEqual({"lat", "lng", "name"}, set(properties))
            location = cls(name="name", lng=5.0, lat=4.2)
            self.assertDictEqual(
                location.dict(), {"lat": 4.2, "lng": 5.0, "name": "name"}
            )
            self.assertEqual(location.test(), "extended")
            self.assertEqual(location.test(return_super=True), "location")

    def test_composite_inheritance(self):
        class Coordinate(models.BaseModel):
            lat = 0.1
            lng = 10.1

        class Name(models.BaseModel):
            name: str

        class Location(Coordinate, Name):
            pass

        self._build_pydantic_classes(Coordinate, Name, Location)
        ClsLocation = self.pydantic_registry[Location.__xreg_name__]
        self.assertTrue(issubclass(ClsLocation, Coordinate))
        self.assertTrue(issubclass(ClsLocation, Name))

        # check that the behaviour is the same for all the definitions
        # of the same model...
        classes = Location, ClsLocation
        for cls in classes:
            properties = cls.schema().get("properties", {}).keys()
            self.assertSetEqual({"lat", "lng", "name"}, set(properties))
            location = cls(name="name", lng=5.0, lat=4.2)
            self.assertDictEqual(
                location.dict(), {"lat": 4.2, "lng": 5.0, "name": "name"}
            )

    def test_model_relation(self):
        class Coordinate(models.BaseModel):
            lat = 0.1
            lng = 10.1

        class Person(models.BaseModel):
            name: str
            coordinate: Coordinate

        class ExtendedCoordinate(Coordinate, extends=Coordinate):
            country: str = None

        self._build_pydantic_classes(Person, Coordinate, ExtendedCoordinate)
        ClsPerson = self.pydantic_registry[Person.__xreg_name__]

        # check that the behaviour is the same for all the definitions
        # of the same model...
        classes = Person, ClsPerson
        for cls in classes:
            person = cls(
                name="test",
                coordinate={"lng": 5.0, "lat": 4.2, "country": "belgium"},
            )
            coordinate = person.coordinate
            self.assertTrue(isinstance(coordinate, Coordinate))
            # sub schema are stored into the definition property
            definitions = ClsPerson.schema().get("definitions", {})
            self.assertIn("Coordinate", definitions)
            coordinate_properties = (
                definitions["Coordinate"].get("properties", {}).keys()
            )
            self.assertSetEqual({"lat", "lng", "country"}, set(coordinate_properties))

    def test_from_orm(self):
        class Group(models.BaseModel):
            name: str

        class User(models.BaseModel):
            name: str
            groups: List[Group] = pydantic.Field(alias="groups_id")  # noqa: F821

        class OrmMode(models.BaseModel):
            class Config:
                orm_mode = True
                getter_dict = utils.GenericOdooGetter

        class GroupOrm(Group, OrmMode, extends=Group):
            pass

        class UserOrm(User, OrmMode, extends=User):
            pass

        self._build_pydantic_classes(Group, User, OrmMode, GroupOrm, UserOrm)
        ClsUser = self.pydantic_registry[User.__xreg_name__]

        # check that the behaviour is the same for all the definitions
        # of the same model...
        classes = User, UserOrm, ClsUser
        odoo_user = self.env.user
        for cls in classes:
            user = cls.from_orm(odoo_user)
            expected = {
                "name": odoo_user.name,
                "groups": [{"name": g.name} for g in odoo_user.groups_id],
            }
            self.assertDictEqual(user.dict(), expected)

    def test_instance(self):
        class Location(models.BaseModel):
            lat = 0.1
            lng = 10.1

        class ExtendedLocation(Location, extends=Location):
            name: str

        self._build_pydantic_classes(Location, ExtendedLocation)

        inst1 = Location.construct()
        inst2 = ExtendedLocation.construct()
        self.assertEqual(inst1.__class__, inst2.__class__)
        self.assertEqual(inst1.schema(), inst2.schema())

    def test_issubclass(self):
        """In this test we check that issublass is lenient when used with
        GenericAlias
        """
        self.assertFalse(issubclass(Literal["test"], models.BaseModel))
        self.assertFalse(issubclass(Literal, models.BaseModel))

        class Location(models.BaseModel):
            kind: Literal["view", "bin"]
            my_list: List[str]

        self._build_pydantic_classes(Location)
        schema = Location.schema()
        self.assertTrue(schema)
