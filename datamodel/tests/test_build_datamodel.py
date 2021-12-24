# Copyright 2017 Camptocamp SA
# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import mock
from marshmallow_objects.models import Model as MarshmallowModel

from odoo import SUPERUSER_ID, api

from .. import fields
from ..core import Datamodel
from .common import DatamodelRegistryCase, TransactionDatamodelCase


class TestBuildDatamodel(DatamodelRegistryCase):
    """Test build of datamodels

    All the tests in this suite are based on the same principle with
    variations:

    * Create new Datamodels (classes inheriting from
      :class:`datamodel.core.Datamodel`
    * Call :meth:`datamodel.core.Datamodel._build_datamodel` on them
      in order to build the 'final class' composed from all the ``_inherit``
      and push it in the datamodels registry (``self.datamodel_registry`` here)
    * Assert that classes are built, registered, have correct ``__bases__``...

    """

    def test_type(self):
        """Ensure that a datamodels are instances of
        marshomallow_objects.Model"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

        class Datamodel2(Datamodel):
            _name = "datamodel2"
            _inherit = "datamodel1"

        self.assertIsInstance(Datamodel1(), MarshmallowModel)
        self.assertIsInstance(Datamodel2(), MarshmallowModel)

    def test_no_name(self):
        """Ensure that a datamodel has a _name"""

        class Datamodel1(Datamodel):
            pass

        msg = ".*must have a _name.*"
        with self.assertRaisesRegex(TypeError, msg):
            Datamodel1._build_datamodel(self.datamodel_registry)

    def test_register(self):
        """Able to register datamodels in datamodels registry"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

        class Datamodel2(Datamodel):
            _name = "datamodel2"

        # build the 'final classes' for the datamodels and check that we find
        # them in the datamodels registry
        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        self.assertEqual(
            ["base", "datamodel1", "datamodel2"], list(self.datamodel_registry)
        )

    def test_inherit_bases(self):
        """Check __bases__ of Datamodel with _inherit"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"
            field_str1 = fields.String(load_default="field_str1")

        class Datamodel2(Datamodel):
            _inherit = "datamodel1"
            field_str2 = fields.String(load_default="field_str2")

        class Datamodel3(Datamodel):
            _inherit = "datamodel1"
            field_str3 = fields.String(load_default="field_str3")

        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        Datamodel3._build_datamodel(self.datamodel_registry)
        self.assertEqual(
            (Datamodel3, Datamodel2, Datamodel1, self.env.datamodels["base"]),
            self.env.datamodels["datamodel1"].__bases__,
        )

    def test_prototype_inherit_bases(self):
        """Check __bases__ of Datamodel with _inherit and different _name"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"
            field_int = fields.Int(load_default=1)

        class Datamodel2(Datamodel):
            _name = "datamodel2"
            _inherit = "datamodel1"
            field_boolean = fields.Boolean(load_default=True)
            field_int = fields.Int(load_default=2)

        class Datamodel3(Datamodel):
            _name = "datamodel3"
            _inherit = "datamodel1"
            field_float = fields.Float(load_default=0.3)

        class Datamodel4(Datamodel):
            _name = "datamodel4"
            _inherit = ["datamodel2", "datamodel3"]

        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        Datamodel3._build_datamodel(self.datamodel_registry)
        Datamodel4._build_datamodel(self.datamodel_registry)
        self.assertEqual(
            (Datamodel1, self.env.datamodels["base"]),
            self.env.datamodels["datamodel1"].__bases__,
        )
        self.assertEqual(
            (
                Datamodel2,
                self.env.datamodels["datamodel1"],
                self.env.datamodels["base"],
            ),
            self.env.datamodels["datamodel2"].__bases__,
        )
        self.assertEqual(
            (
                Datamodel3,
                self.env.datamodels["datamodel1"],
                self.env.datamodels["base"],
            ),
            self.env.datamodels["datamodel3"].__bases__,
        )
        self.assertEqual(
            (
                Datamodel4,
                self.env.datamodels["datamodel2"],
                self.env.datamodels["datamodel3"],
                self.env.datamodels["base"],
            ),
            self.env.datamodels["datamodel4"].__bases__,
        )

    def test_final_class_schema(self):
        """Check the MArshmallow schema of the final class"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"
            field_int = fields.Int(load_default=1)

        class Datamodel2(Datamodel):
            _name = "datamodel2"
            _inherit = "datamodel1"
            field_boolean = fields.Boolean(load_default=True)
            field_int = fields.Int(load_default=2)

        class Datamodel3(Datamodel):
            _name = "datamodel3"
            _inherit = "datamodel1"
            field_float = fields.Float(load_default=0.3)

        class Datamodel4(Datamodel):
            _name = "datamodel4"
            _inherit = ["datamodel2", "datamodel3"]

        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        Datamodel3._build_datamodel(self.datamodel_registry)
        Datamodel4._build_datamodel(self.datamodel_registry)

        Datamodel1 = self.env.datamodels["datamodel1"]
        Datamodel2 = self.env.datamodels["datamodel2"]
        Datamodel3 = self.env.datamodels["datamodel3"]
        Datamodel4 = self.env.datamodels["datamodel4"]

        self.assertEqual(Datamodel1().dump(), {"field_int": 1})
        self.assertDictEqual(
            Datamodel2().dump(), {"field_boolean": True, "field_int": 2}
        )
        self.assertDictEqual(Datamodel3().dump(), {"field_float": 0.3, "field_int": 1})
        self.assertDictEqual(
            Datamodel4().dump(),
            {"field_boolean": True, "field_int": 2, "field_float": 0.3},
        )

    def test_custom_build(self):
        """Check that we can hook at the end of a Datamodel build"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

            @classmethod
            def _complete_datamodel_build(cls):
                # This method should be called after the Datamodel
                # is built, and before it is pushed in the registry
                cls._build_done = True

        Datamodel1._build_datamodel(self.datamodel_registry)
        # we inspect that our custom build has been executed
        self.assertTrue(self.env.datamodels["datamodel1"]._build_done)

    def test_inherit_attrs(self):
        """Check attributes inheritance of Datamodels with _inherit"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

            msg = "ping"

            def say(self):
                return "foo"

        class Datamodel2(Datamodel):
            _name = "datamodel2"
            _inherit = "datamodel1"

            msg = "pong"

            def say(self):
                return super(Datamodel2, self).say() + " bar"

        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        # we initialize the datamodels, normally we should pass
        # an instance of WorkContext, but we don't need a real one
        # for this test
        datamodel1 = self.env.datamodels["datamodel1"](mock.Mock())
        datamodel2 = self.env.datamodels["datamodel2"](mock.Mock())
        self.assertEqual("ping", datamodel1.msg)
        self.assertEqual("pong", datamodel2.msg)
        self.assertEqual("foo", datamodel1.say())
        self.assertEqual("foo bar", datamodel2.say())

    def test_duplicate_datamodel(self):
        """Check that we can't have 2 datamodels with the same name"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

        class Datamodel2(Datamodel):
            _name = "datamodel1"

        Datamodel1._build_datamodel(self.datamodel_registry)
        msg = "Datamodel.*already exists.*"
        with self.assertRaisesRegex(TypeError, msg):
            Datamodel2._build_datamodel(self.datamodel_registry)

    def test_no_parent(self):
        """Ensure we can't _inherit a non-existent datamodel"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"
            _inherit = "datamodel1"

        msg = "Datamodel.*does not exist in registry.*"
        with self.assertRaisesRegex(TypeError, msg):
            Datamodel1._build_datamodel(self.datamodel_registry)

    def test_no_parent2(self):
        """Ensure we can't _inherit by prototype a non-existent datamodel"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

        class Datamodel2(Datamodel):
            _name = "datamodel2"
            _inherit = ["datamodel1", "datamodel3"]

        Datamodel1._build_datamodel(self.datamodel_registry)
        msg = "Datamodel.*inherits from non-existing datamodel.*"
        with self.assertRaisesRegex(TypeError, msg):
            Datamodel2._build_datamodel(self.datamodel_registry)

    def test_add_inheritance(self):
        """Ensure we can add a new inheritance"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"

        class Datamodel2(Datamodel):
            _name = "datamodel2"

        class Datamodel2bis(Datamodel):
            _name = "datamodel2"
            _inherit = ["datamodel2", "datamodel1"]

        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        Datamodel2bis._build_datamodel(self.datamodel_registry)

        self.assertEqual(
            (
                Datamodel2bis,
                Datamodel2,
                self.env.datamodels["datamodel1"],
                self.env.datamodels.registry.get("base"),
            ),
            self.env.datamodels["datamodel2"].__bases__,
        )

    def test_add_inheritance_final_schema(self):
        """Ensure that the Marshmallow schema is updated if we add a
        new inheritance"""

        class Datamodel1(Datamodel):
            _name = "datamodel1"
            field_str1 = fields.String(load_default="str1")

        class Datamodel2(Datamodel):
            _name = "datamodel2"
            field_str2 = fields.String(load_default="str2")

        class Datamodel2bis(Datamodel):
            _name = "datamodel2"
            _inherit = ["datamodel2", "datamodel1"]
            field_str3 = fields.String(load_default="str3")

        Datamodel1._build_datamodel(self.datamodel_registry)
        Datamodel2._build_datamodel(self.datamodel_registry)
        Datamodel2bis._build_datamodel(self.datamodel_registry)

        Datamodel2 = self.env.datamodels["datamodel2"]
        self.assertDictEqual(
            Datamodel2().dump(),
            {"field_str1": "str1", "field_str2": "str2", "field_str3": "str3"},
        )

    def test_recursion(self):
        class Datamodel1(Datamodel):
            _name = "datamodel1"
            field_str = fields.String()

        Datamodel1._build_datamodel(self.datamodel_registry)
        for _i in range(0, 1000):
            self.env.datamodels["datamodel1"](field_str="1234")

    def test_nested_model(self):
        """Test nested model serialization/deserialization"""

        class Parent(Datamodel):
            _name = "parent"
            name = fields.String()
            child = fields.NestedModel("child")

        class Child(Datamodel):
            _name = "child"
            field_str = fields.String()

        Parent._build_datamodel(self.datamodel_registry)
        Child._build_datamodel(self.datamodel_registry)

        Parent = self.env.datamodels["parent"]
        Child = self.env.datamodels["child"]

        instance = Parent(name="Parent", child=Child(field_str="My other string"))
        res = instance.dump()
        self.assertDictEqual(
            res, {"child": {"field_str": "My other string"}, "name": "Parent"}
        )
        new_instance = instance.load(res)
        self.assertEqual(new_instance.name, instance.name)
        self.assertEqual(new_instance.child.field_str, instance.child.field_str)

    def test_list_nested_model(self):
        """Test list model of nested model serialization/deserialization"""

        class Parent(Datamodel):
            _name = "parent"
            name = fields.String()
            list_child = fields.List(fields.NestedModel("child"))

        class Child(Datamodel):
            _name = "child"
            field_str = fields.String()

        Parent._build_datamodel(self.datamodel_registry)
        Child._build_datamodel(self.datamodel_registry)

        Parent = self.env.datamodels["parent"]
        Child = self.env.datamodels["child"]

        childs = [
            Child(field_str="My 1st other string"),
            Child(field_str="My 2nd other string"),
        ]
        instance = Parent(name="Parent", list_child=childs)
        res = instance.dump()
        self.assertDictEqual(
            res,
            {
                "list_child": [
                    {"field_str": "My 1st other string"},
                    {"field_str": "My 2nd other string"},
                ],
                "name": "Parent",
            },
        )
        new_instance = instance.load(res)
        self.assertEqual(new_instance.name, instance.name)
        self.assertEqual(new_instance.list_child, instance.list_child)

    def test_many(self):
        """Test loads of many"""

        class Item(Datamodel):
            _name = "item"
            idx = fields.Integer()

        Item._build_datamodel(self.datamodel_registry)
        Item = self.env.datamodels["item"]

        items = Item.load([{"idx": 1}, {"idx": 2}], many=True)
        self.assertTrue(len(items), 2)
        self.assertEqual([i.idx for i in items], [1, 2])

    def test_nested_many(self):
        """Tests loads and dump of model with array of nested model"""

        class Parent(Datamodel):
            _name = "parent"
            items = fields.NestedModel("item", many=True)

        class Item(Datamodel):
            _name = "item"
            idx = fields.Integer()

        Parent._build_datamodel(self.datamodel_registry)
        Item._build_datamodel(self.datamodel_registry)

        Parent = self.env.datamodels["parent"]
        Item = self.env.datamodels["item"]

        instance = Parent.load({"items": [{"idx": 1}, {"idx": 2}]})
        res = instance.dump()
        self.assertEqual(res, {"items": [{"idx": 1}, {"idx": 2}]})
        new_instance = Parent.load(res)
        self.assertEqual(len(new_instance.items), 2)
        self.assertEqual([i.idx for i in new_instance.items], [1, 2])
        new_instance.items.append(Item(idx=3))
        res = new_instance.dump()
        self.assertEqual(res, {"items": [{"idx": 1}, {"idx": 2}, {"idx": 3}]})

    def test_env(self):
        """
        Tests that the current env is always available on datamodel instances
        and schema
        """

        class Parent(Datamodel):
            _name = "parent"
            items = fields.NestedModel("item", many=True)

        class Item(Datamodel):
            _name = "item"
            idx = fields.Integer()

        Parent._build_datamodel(self.datamodel_registry)
        Item._build_datamodel(self.datamodel_registry)
        Parent = self.env.datamodels["parent"]
        p = Parent()
        self.assertEqual(p.env, self.env)
        schema = Parent.get_schema()
        self.assertEqual(schema._env, self.env)
        instance = Parent.load({"items": [{"idx": 1}, {"idx": 2}]})
        self.assertEqual(instance.items[0].env, self.env)
        schema = instance.items[0].get_schema()
        self.assertEqual(schema._env, self.env)
        another_env = api.Environment(self.env.registry.cursor(), SUPERUSER_ID, {})
        new_p = another_env.datamodels["parent"]()
        self.assertEqual(new_p.env, another_env)


class TestRegistryAccess(TransactionDatamodelCase):
    def test_registry_access(self):
        """Check the access to the registry directly on tnv"""
        base = self.env.datamodels["base"]
        self.assertIsInstance(base(), MarshmallowModel)
