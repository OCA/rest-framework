# Copyright 2017 Camptocamp SA
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import functools
import logging
from collections import OrderedDict, defaultdict

from odoo.api import Environment
from odoo.tools import LastOrderedSet, OrderedSet

_logger = logging.getLogger(__name__)

try:
    import marshmallow
    from marshmallow_objects.models import Model as MarshmallowModel, ModelMeta
except ImportError:
    _logger.debug("Cannot import 'marshmallow_objects'.")


# The Cache size represents the number of items, so the number
# of datamodels (include abstract datamodels) we will keep in the LRU
# cache. We would need stats to know what is the average but this is a bit
# early.
DEFAULT_CACHE_SIZE = 512


# this is duplicated from odoo.models.MetaModel._get_addon_name() which we
# unfortunately can't use because it's an instance method and should have been
# a @staticmethod
def _get_addon_name(full_name):
    # The (Odoo) module name can be in the ``odoo.addons`` namespace
    # or not. For instance, module ``sale`` can be imported as
    # ``odoo.addons.sale`` (the right way) or ``sale`` (for backward
    # compatibility).
    module_parts = full_name.split(".")
    if len(module_parts) > 2 and module_parts[:2] == ["odoo", "addons"]:
        addon_name = module_parts[2]
    else:
        addon_name = module_parts[0]
    return addon_name


class DatamodelDatabases(dict):
    """ Holds a registry of datamodels for each database """


class DatamodelRegistry(object):
    """Store all the datamodel and allow to retrieve them by name

    The key is the ``_name`` of the datamodels.

    This is an OrderedDict, because we want to keep the registration order of
    the datamodels, addons loaded first have their datamodels found first.

    The :attr:`ready` attribute must be set to ``True`` when all the datamodels
    are loaded.

    """

    def __init__(self, cachesize=DEFAULT_CACHE_SIZE):
        self._datamodels = OrderedDict()
        self._loaded_modules = set()
        self.ready = False

    def __getitem__(self, key):
        return self._datamodels[key]

    def __setitem__(self, key, value):
        self._datamodels[key] = value

    def __contains__(self, key):
        return key in self._datamodels

    def get(self, key, default=None):
        return self._datamodels.get(key, default)

    def __iter__(self):
        return iter(self._datamodels)

    def load_datamodels(self, module):
        if module in self._loaded_modules:
            return
        for datamodel_class in MetaDatamodel._modules_datamodels[module]:
            datamodel_class._build_datamodel(self)
        self._loaded_modules.add(module)


# We will store a DatamodeltRegistry per database here,
# it will be cleared and updated when the odoo's registry is rebuilt
_datamodel_databases = DatamodelDatabases()


@marshmallow.post_load
def __make_object__(self, data, **kwargs):
    datamodel = self._env.datamodels[self._datamodel_name]
    return datamodel(__post_load__=True, __schema__=self, **data)


class MetaDatamodel(ModelMeta):
    """Metaclass for Datamodel

    Every new :class:`Datamodel` will be added to ``_modules_datamodels``,
    that will be used by the datamodel builder.

    """

    _modules_datamodels = defaultdict(list)

    def __init__(self, name, bases, attrs):

        if not self._register:
            self._register = True
            super(MetaDatamodel, self).__init__(name, bases, attrs)

            return

        # If datamodels are declared in tests, exclude them from the
        # "datamodels of the addon" list. If not, when we use the
        # "load_datamodels" method, all the test datamodels would be loaded.
        # This should never be an issue when running the app normally, as the
        # Python tests should never be executed. But this is an issue when a
        # test creates a test datamodels for the purpose of the test, then a
        # second tests uses the "load_datamodels" to load all the addons of the
        # module: it will load the datamodel of the previous test.
        if "tests" in self.__module__.split("."):
            return

        if not hasattr(self, "_module"):
            self._module = _get_addon_name(self.__module__)

        self._modules_datamodels[self._module].append(self)


class Datamodel(MarshmallowModel, metaclass=MetaDatamodel):
    """Main Datamodel Model

    All datamodels have a Python inheritance either on
    :class:`Datamodel`.

    Inheritance mechanism
        The inheritance mechanism is like the Odoo's one for Models.  Each
        datamodel has a ``_name``. This is the absolute minimum in a Datamodel
        class.

        ::

            from marshmallow import fields
            from odoo.addons.datamodel.core import Datamodel

            class MyDatamodel(Datamodel):
                _name = 'my.datamodel'

                name = fields.String()

        Every datamodel implicitly inherit from the `'base'` datamodel.

        There are two close but distinct inheritance types, which look
        familiar if you already know Odoo.  The first uses ``_inherit`` with
        an existing name, the name of the datamodel we want to extend.  With
        the following example, ``my.datamodel`` is now able to speak and to
        yell.

        ::

            class MyDatamodel(Datamodel):  # name of the class does not matter
                _inherit = 'my.datamodel'


        The second has a different ``_name``, it creates a new datamodel,
        including the behavior of the inherited datamodel, but without
        modifying it.

        ::

            class AnotherDatamodel(Datamodel):
                _name = 'another.datamodel'
                _inherit = 'my.datamodel'

                age = fields.Int()
    """

    _register = False
    _env = None  # Odoo Environment

    # used for inheritance
    _name = None  #: Name of the datamodel

    #: Name or list of names of the datamodel(s) to inherit from
    _inherit = None

    def __init__(self, context=None, partial=None, env=None, **kwargs):
        self._env = env
        super().__init__(context=context, partial=partial, **kwargs)

    @property
    def env(self):
        """ Current datamodels registry"""
        return self._env

    @classmethod
    def get_schema(cls, **kwargs):
        """
        Get a marshmallow schema instance
        :param kwargs:
        :return:
        """
        return cls.__get_schema_class__(**kwargs)

    @classmethod
    def _build_datamodel(cls, registry):
        """Instantiate a given Datamodel in the datamodels registry.

        This method is called at the end of the Odoo's registry build.  The
        caller is :meth:`datamodel.builder.DatamodelBuilder.load_datamodels`.

        It generates new classes, which will be the Datamodel classes we will
        be using.  The new classes are generated following the inheritance
        of ``_inherit``. It ensures that the ``__bases__`` of the generated
        Datamodel classes follow the ``_inherit`` chain.

        Once a Datamodel class is created, it adds it in the Datamodel Registry
        (:class:`DatamodelRegistry`), so it will be available for
        lookups.

        At the end of new class creation, a hook method
        :meth:`_complete_datamodel_build` is called, so you can customize
        further the created datamodels.

        The following code is roughly the same than the Odoo's one for
        building Models.

        """

        # In the simplest case, the datamodel's registry class inherits from
        # cls and the other classes that define the datamodel in a flat
        # hierarchy.  The registry contains the instance ``datamodel`` (on the
        # left). Its class, ``DatamodelClass``, carries inferred metadata that
        # is shared between all the datamodel's instances for this registry
        # only.
        #
        #   class A1(Datamodel):                    Datamodel
        #       _name = 'a'                           / | \
        #                                            A3 A2 A1
        #   class A2(Datamodel):                      \ | /
        #       _inherit = 'a'                    DatamodelClass
        #
        #   class A3(Datamodel):
        #       _inherit = 'a'
        #
        # When a datamodel is extended by '_inherit', its base classes are
        # modified to include the current class and the other inherited
        # datamodel classes.
        # Note that we actually inherit from other ``DatamodelClass``, so that
        # extensions to an inherited datamodel are immediately visible in the
        # current datamodel class, like in the following example:
        #
        #   class A1(Datamodel):
        #       _name = 'a'                          Datamodel
        #                                            /  / \  \
        #   class B1(Datamodel):                    /  A2 A1  \
        #       _name = 'b'                        /   \  /    \
        #                                         B2 DatamodelA B1
        #   class B2(Datamodel):                   \     |     /
        #       _name = 'b'                         \    |    /
        #       _inherit = ['b', 'a']                \   |   /
        #                                            DatamodelB
        #   class A2(Datamodel):
        #       _inherit = 'a'

        # determine inherited datamodels
        parents = cls._inherit
        if isinstance(parents, str):
            parents = [parents]
        elif parents is None:
            parents = []

        if cls._name in registry and not parents:
            raise TypeError(
                "Datamodel %r (in class %r) already exists. "
                "Consider using _inherit instead of _name "
                "or using a different _name." % (cls._name, cls)
            )

        # determine the datamodel's name
        name = cls._name or (len(parents) == 1 and parents[0])

        if not name:
            raise TypeError("Datamodel %r must have a _name" % cls)

        # all datamodels except 'base' implicitly inherit from 'base'
        if name != "base":
            parents = list(parents) + ["base"]

        # create or retrieve the datamodel's class
        if name in parents:
            if name not in registry:
                raise TypeError("Datamodel %r does not exist in registry." % name)

        # determine all the classes the datamodel should inherit from
        bases = LastOrderedSet([cls])
        for parent in parents:
            if parent not in registry:
                raise TypeError(
                    "Datamodel %r inherits from non-existing datamodel %r."
                    % (name, parent)
                )
            parent_class = registry[parent]
            if parent == name:
                for base in parent_class.__bases__:
                    bases.add(base)
            else:
                bases.add(parent_class)
                parent_class._inherit_children.add(name)

        if name in parents:
            DatamodelClass = registry[name]
            # Add the new bases to the existing model since the class into
            # the registry could already be used into an inherit
            DatamodelClass.__bases__ = tuple(bases)
            # We must update the marshmallow schema on the existing datamodel
            # class to include those inherited
            parent_schemas = []
            for parent in bases:
                if issubclass(parent, MarshmallowModel):
                    parent_schemas.append(parent.__schema_class__)
            schema_class = type(name + "Schema", tuple(parent_schemas), {})
            DatamodelClass.__schema_class__ = schema_class
        else:
            attrs = {
                "_name": name,
                "_register": False,
                # names of children datamodel
                "_inherit_children": OrderedSet(),
            }
            if name == "base":
                attrs["_registry"] = registry
            DatamodelClass = type(name, tuple(bases), attrs)

        setattr(DatamodelClass.__schema_class__, "_registry", registry)  # noqa: B010
        setattr(DatamodelClass.__schema_class__, "_datamodel_name", name)  # noqa: B010
        setattr(  # noqa: B010
            DatamodelClass.__schema_class__, "__make_object__", __make_object__
        )
        DatamodelClass._complete_datamodel_build()

        registry[name] = DatamodelClass

        return DatamodelClass

    @classmethod
    def _complete_datamodel_build(cls):
        """Complete build of the new datamodel class

        After the datamodel has been built from its bases, this method is
        called, and can be used to customize the class before it can be used.

        Nothing is done in the base Datamodel, but a Datamodel can inherit
        the method to add its own behavior.
        """


# makes the datamodels registry available on env


class DataModelFactory(object):
    """Factory for datamodels

    This factory ensures the propagation of the environment to the
    instanciated datamodels and related schema.
    """

    __slots__ = ("env", "registry")

    def __init__(self, env, registry):
        self.env = env
        self.registry = registry

    def __getitem__(self, key):
        model = self.registry[key]
        model.__init__ = functools.partialmethod(model.__init__, env=self.env)

        @classmethod
        def __get_schema_class__(cls, **kwargs):
            cls = cls.__schema_class__(**kwargs)
            cls._env = self.env
            return cls

        model.__get_schema_class__ = __get_schema_class__
        return model


@property
def datamodels(self):
    if not hasattr(self, "_datamodels_factory"):
        factory = DataModelFactory(self, _datamodel_databases.get(self.cr.dbname))
        self._datamodels_factory = factory
    return self._datamodels_factory


Environment.datamodels = datamodels
