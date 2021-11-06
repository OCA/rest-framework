# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from typing import Dict, List, Optional, Set

from odoo.api import Environment
from odoo.tools import LastOrderedSet

from pydantic.typing import update_field_forward_refs

from .models import BaseModel, ModelType


class PydanticClassDef(object):
    name: str = None
    hierarchy: List[ModelType] = None
    base_names: Set[str] = None

    def __init__(self, cls: ModelType):
        self.name = cls._name
        self.hierarchy = [cls]
        self.base_names = set(cls._inherit or [])

    def add_child(self, cls: ModelType):
        self.hierarchy.append(cls)
        for base in cls._inherit:
            self.base_names.add(base)

    @property
    def is_mixed_bases(self) -> bool:
        return set(self.name) != self.base_names


class PydanticClassDefsRegistry(dict):
    pass


class PydanticClassesDatabases(dict):
    """ Holds a registry of pydantic classes for each database """


class PydanticClassesRegistry(object):
    """Store all the PydanticClasses and allow to retrieve them by name

    The key is the ``_name`` of the pydantic classes.

    The :attr:`ready` attribute must be set to ``True`` when all the pydantic classes
    are loaded.

    """

    def __init__(self):
        self._pydantic_classes: Dict[str, ModelType] = {}
        self._loaded_modules: Set[str] = set()
        self.ready: bool = False
        self._pydantic_class_defs: Dict[
            str, PydanticClassDef
        ] = PydanticClassDefsRegistry()

    def __getitem__(self, key: str) -> ModelType:
        return self._pydantic_classes[key]

    def __setitem__(self, key: str, value: ModelType):
        self._pydantic_classes[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._pydantic_classes

    def get(self, key: str, default: Optional[ModelType] = None) -> ModelType:
        return self._pydantic_classes.get(key, default)

    def __iter__(self):
        return iter(self._pydantic_classes)

    def load_pydantic_classes(self, module: str):
        if module in self._loaded_modules:
            return
        for cls in BaseModel._pydantic_classes_by_module[module]:
            self.load_pydantic_class_def(cls)
        self._loaded_modules.add(module)

    def load_pydantic_class_def(self, cls: ModelType):
        parents = cls._inherit
        if cls._name in self and not parents:
            raise TypeError(f"Pydantic {cls._name} (in class {cls}) already exists.")
        class_def = self._pydantic_class_defs.get(cls._name)
        if not class_def:
            self._pydantic_class_defs[cls._name] = PydanticClassDef(cls)
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
                remaining.append(name, class_def)
            to_build = remaining

    def build_pydantic_class(self, class_def: PydanticClassDef) -> ModelType:
        """
        Build the class hierarchy from the first one to the last one into
        the hierachy definition.
        """
        name = class_def.name
        for cls in class_def.hierarchy:
            # retrieve pydantic_parent
            # determine all the classes the component should inherit from
            bases = LastOrderedSet([cls])
            for base_name in cls._inherit:
                if base_name not in self:
                    raise TypeError(
                        f"Pydnatic class '{name}' extends an non-existing "
                        f"pydantic class '{base_name}'."
                    )
                parent_class = self[base_name]
                bases.add(parent_class)

            uniq_class_name = f"{name}_{id(cls)}"
            PydanticClass = type(
                name,
                tuple(bases),
                {
                    # attrs for pickle to find this class
                    "__module__": __name__,
                    "__qualname__": uniq_class_name,
                },
            )
            base = PydanticClass
            self[name] = base
        return base

    def update_forward_refs(self):
        """Try to update ForwardRefs on fields to resolve dynamic type usage."""
        for cls in self._pydantic_classes.values():
            for f in cls.__fields__.values():
                update_field_forward_refs(f, {}, self)


# We will store a PydanticClassestRegistry per database here,
# it will be cleared and updated when the odoo's registry is rebuilt
_pydantic_classes_databases = PydanticClassesDatabases()


@property
def pydantic_registry(self):
    if not hasattr(self, "_pydantic_registry"):
        self._pydantic_registry = _pydantic_classes_databases.get(self.cr.dbname)
    return self._pydantic_registry


Environment.pydantic_registry = pydantic_registry
