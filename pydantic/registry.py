# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
from contextlib import contextmanager
from typing import Dict, List, Optional, Set

from odoo.tools import LastOrderedSet

from pydantic.utils import ClassAttribute

from . import models


class PydanticClassDef(object):
    name: str = None
    hierarchy: List[models.ModelType] = None
    base_names: Set[str] = None

    def __init__(self, cls):
        self.name = cls.__xreg_name__
        self.hierarchy = [cls]
        self.base_names = set(cls.__xreg_base_names__ or [])

    def add_child(self, cls):
        self.hierarchy.append(cls)
        for base in cls.__xreg_base_names__:
            self.base_names.add(base)

    @property
    def is_mixed_bases(self):
        return set(self.name) != self.base_names

    def __repr__(self):
        return f"PydanticClassDef {self.name}"


class PydanticClassDefsRegistry(dict):
    pass


class PydanticClassesDatabases(dict):
    """ Holds a registry of pydantic classes for each database """


class PydanticClassesRegistry(object):
    """Store all the PydanticClasses and allow to retrieve them by name

    The key is the ``cls.__module__ + "." + cls.__qualname__`` of the
    pydantic classes.

    The :attr:`ready` attribute must be set to ``True`` when all the pydantic classes
    are loaded.

    """

    def __init__(self):
        self._pydantic_classes: Dict[str, models.ModelType] = {}
        self._loaded_modules: Set[str] = set()
        self.ready: bool = False
        self._pydantic_class_defs: Dict[
            str, PydanticClassDef
        ] = PydanticClassDefsRegistry()

    def __getitem__(self, key: str) -> models.ModelType:
        return self._pydantic_classes[key]

    def __setitem__(self, key: str, value: models.ModelType):
        self._pydantic_classes[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._pydantic_classes

    def get(
        self, key: str, default: Optional[models.ModelType] = None
    ) -> models.ModelType:
        return self._pydantic_classes.get(key, default)

    def __iter__(self):
        return iter(self._pydantic_classes)

    def load_pydantic_classes(self, module: str):
        if module in self._loaded_modules:
            return
        for cls in models.BaseModel._pydantic_classes_by_module.get(module, []):
            self.load_pydantic_class_def(cls)
        self._loaded_modules.add(module)

    def load_pydantic_class_def(self, cls: models.ModelType):
        parents = cls.__xreg_base_names__
        if cls.__xreg_name__ in self and not parents:
            raise TypeError(
                f"Pydantic {cls.__xreg_name__} (in class {cls}) already exists."
            )
        class_def = self._pydantic_class_defs.get(cls.__xreg_name__)
        if not class_def:
            self._pydantic_class_defs[cls.__xreg_name__] = PydanticClassDef(cls)
        else:
            class_def.add_child(cls)

    def build_pydantic_classes(self):
        """,
        We iterate over all the class definitions and build the final
        hierarchy.
        """
        # we first check that all bases are defined
        for class_def in self._pydantic_class_defs.values():
            for base in class_def.base_names:
                if base not in self._pydantic_class_defs:
                    raise TypeError(
                        f"Pydantic class '{class_def.name}' inherits from"
                        f"undefined base '{base}'"
                    )
        to_build = self._pydantic_class_defs.items()
        while to_build:
            remaining = []
            for name, class_def in self._pydantic_class_defs.items():
                if not class_def.is_mixed_bases:
                    self.build_pydantic_class(class_def)
                    continue
                # Generate only class with all the bases into the registry
                all_in_registry = True
                for base in class_def.base_names:
                    if base == name:
                        continue
                    if base not in self:
                        all_in_registry = False
                        break
                if all_in_registry:
                    self.build_pydantic_class(class_def)
                    continue
                remaining.append((name, class_def))
            to_build = remaining

    def build_pydantic_class(self, class_def: PydanticClassDef) -> models.ModelType:
        """
        Build the class hierarchy from the first one to the last one into
        the hierachy definition.
        """
        name = class_def.name
        for cls in class_def.hierarchy:
            # retrieve pydantic_parent
            # determine all the classes the component should inherit from
            bases = LastOrderedSet([cls])
            for base_name in cls.__xreg_base_names__:
                if base_name not in self:
                    raise TypeError(
                        f"Pydnatic class '{name}' extends an non-existing "
                        f"pydantic class '{base_name}'."
                    )
                parent_class = self[base_name]
                bases.add(parent_class)
            simple_name = name.split(".")[-1]
            uniq_class_name = f"{simple_name}_{id(cls)}"
            PydanticClass = type(
                simple_name,
                tuple(bases),
                {
                    # attrs for pickle to find this class
                    "__module__": cls.__module__,
                    "__qualname__": uniq_class_name,
                    "_is_aggregated_class": ClassAttribute(
                        "_is_aggregated_class", True
                    ),
                },
            )
            base = PydanticClass
            self[name] = base
        return base

    def update_forward_refs(self):
        """Try to update ForwardRefs on fields to resolve dynamic type usage."""
        for cls in self._pydantic_classes.values():
            cls.update_forward_refs()

    def resolve_submodel_fields(self):
        for cls in self._pydantic_classes.values():
            cls._resolve_submodel_fields(registry=self)

    @contextmanager
    def build_mode(self):
        models._registry_build_mode = True
        try:
            yield
        finally:
            models._registry_build_mode = False

    def init_registry(self, modules: List[str] = None):
        """
        Build the pydantic classes by aggregating the classes declared
        in the given module list in the same as the list one. IOW, the mro
        into the aggregated classes will be the inverse one of the given module
        list. If no module list given, build the aggregated classes for all the
        modules loaded by the metaclass in the same order as the loading process
        """
        # Thes list of module should shoudl be build from the graph of module
        # dependencies. The order of this list represent the list of modules
        # from the most generic one to the most specialized one.
        # We walk through the graph to build the definition of the classes
        # to assemble. The goal is to have for each class name the final
        # picture of all the fragments required to build the right hierarchy.
        # It's required to avoid to change the bases of an already build class
        # each time a module extend the initial implementation as Odoo is
        # doing with `Model`. The final definition of a class could depend on
        # the potential metaclass associated to the class (a metaclass is a
        # class factory). It's therefore not safe to modify on the fly
        # the __bases__ attribute of a class once it's constructed since
        # the factory method of the metaclass depends on these 'bases'
        # __new__(mcs, name, bases, new_namespace, **kwargs).
        # 'bases' could therefore be processed by the factory in a way or an
        # other to build the final class. If you modify the bases after the
        # class creation, the logic implemented by the factory will not be
        # applied to the new bases and your class could be in an incoherent
        # state.
        modules = (
            modules if modules else models.BaseModel._pydantic_classes_by_module.keys()
        )
        with self.build_mode():
            for module in modules:
                self.load_pydantic_classes(module)
            self.build_pydantic_classes()
            self.update_forward_refs()
            self.resolve_submodel_fields()
        self.ready = True


# We will store a PydanticClassestRegistry per database here,
# it will be cleared and updated when the odoo's registry is rebuilt
_pydantic_classes_databases = PydanticClassesDatabases()
