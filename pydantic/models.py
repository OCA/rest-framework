# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
import collections
import functools
import inspect
from typing import Any, List, TypeVar, no_type_check

try:
    from typing import OrderedDict
except ImportError:
    from typing import Dict as OrderedDict

import pydantic
from pydantic.fields import ModelField
from pydantic.main import ModelMetaclass
from pydantic.utils import ClassAttribute

from . import utils
from .context import odoo_pydantic_registry

ModelType = TypeVar("Model", bound="BaseModel")

_is_base_model_class_defined = False
_registry_build_mode = False


class ExtendablePydanticModelMeta(ModelMetaclass):
    @no_type_check
    def __new__(cls, clsname, bases, namespace, extends=None, **kwargs):
        """create a expected class and a fragment class that will
        be assembled at the end of registry load process
        to build the final class.
        """
        if _is_base_model_class_defined:
            registry_name = ".".join(
                (namespace["__module__"], namespace["__qualname__"])
            )
            if extends:
                # if we extends an other BaseModel, the registry name must
                # be the one from the extended BaseModel
                if not issubclass(extends, BaseModel):
                    raise TypeError(
                        f"Pyndatic class {registry_name} extends an non "
                        f"pytdantic class {extends.__name__} "
                    )
                registry_name = getattr(extends, "__xreg_name__", None)
            registry_base_names = [
                b.__xreg_name__
                for b in bases
                if issubclass(b, BaseModel) and b != BaseModel
            ]
            namespace.update(
                {
                    "__xreg_name__": ClassAttribute("__xreg_name__", registry_name),
                    "__xreg_base_names__": ClassAttribute(
                        "__xreg_base_names__", registry_base_names
                    ),
                }
            )
            # for the original class, we wrap the class methods to forward
            # the call to the aggregated one at runtime
            new_namespace = cls._wrap_class_methods(namespace)
        else:
            # here we are into the instanciation fo BaseModel
            # we must wrap all the classmethod defined into pydantic.BaseModel
            new_namespace = cls._wrap_pydantic_base_model_class_methods(namespace)
        assembly_frag_cls = None
        if _is_base_model_class_defined and not _registry_build_mode:
            # we are into the loading process of original BaseModel
            # For each defined BaseModel class, we create and register the
            # corresponding fragment to be aggregated into the final class
            other_bases = [BaseModel] + [
                b for b in bases if not (issubclass(b, BaseModel))
            ]
            namespace.update({"__qualname__": namespace["__qualname__"] + "Frag"})
            assembly_frag_cls = super().__new__(
                cls,
                name=clsname + "Frag",
                bases=tuple(other_bases),
                namespace=namespace,
                **kwargs,
            )
            assembly_frag_cls.__register__()

        # We build the Origial class
        new_cls = super().__new__(
            cls, name=clsname, bases=bases, namespace=new_namespace, **kwargs
        )
        if assembly_frag_cls:
            assembly_frag_cls._original_cls = ClassAttribute("_original_cls", new_cls)
        return new_cls

    @classmethod
    def _wrap_class_methods(cls, namespace):
        new_namespace = {}
        for key, value in namespace.items():
            if isinstance(value, classmethod):
                func = value.__func__

                def new_method(
                    cls, *args, _method_name=None, _initial_func=None, **kwargs
                ):
                    # ensure that arggs and kwargs are conform to the
                    # initial signature
                    inspect.signature(_initial_func).bind(cls, *args, **kwargs)
                    return getattr(cls._get_assembled_cls(), _method_name)(
                        *args, **kwargs
                    )

                new_method_def = functools.partial(
                    new_method, _method_name=key, _initial_func=func
                )
                # preserve signature for IDE
                functools.update_wrapper(new_method_def, func)
                new_namespace[key] = classmethod(new_method_def)
            else:
                new_namespace[key] = value
        return new_namespace

    @classmethod
    def _wrap_pydantic_base_model_class_methods(cls, namespace):
        new_namespace = namespace
        methods = inspect.getmembers(pydantic.BaseModel, inspect.ismethod)
        for name, method in methods:
            func = method.__func__
            if name.startswith("__"):
                continue
            if name in namespace:
                continue

            def new_method(cls, *args, _method_name=None, _initial_func=None, **kwargs):
                # ensure that arggs and kwargs are conform to the
                # initial signature
                inspect.signature(_initial_func).bind(cls, *args, **kwargs)
                if getattr(cls, "_is_aggregated_class", False) or hasattr(
                    cls, "_original_cls"
                ):
                    return _initial_func(cls, *args, **kwargs)
                cls = cls._get_assembled_cls()
                return getattr(cls, _method_name)(*args, **kwargs)

            new_method_def = functools.partial(
                new_method, _method_name=name, _initial_func=func
            )
            # preserve signature for IDE
            functools.update_wrapper(new_method_def, func)
            new_namespace[name] = classmethod(new_method_def)
        return new_namespace

    def __subclasscheck__(cls, subclass):  # noqa: B902
        """Implement issubclass(sub, cls)."""
        if hasattr(subclass, "_original_cls"):
            return cls.__subclasscheck__(subclass._original_cls)
        return isinstance(subclass, type) and super().__subclasscheck__(subclass)


class BaseModel(pydantic.BaseModel, metaclass=ExtendablePydanticModelMeta):
    _pydantic_classes_by_module: OrderedDict[
        str, List[ModelType]
    ] = collections.OrderedDict()

    def __new__(cls, *args, **kwargs):
        if getattr(cls, "_is_aggregated_class", False):
            return super().__new__(cls)
        return cls._get_assembled_cls()(*args, **kwargs)

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        for b in cls.__bases__:
            if issubclass(b, BaseModel):
                b.update_forward_refs(**localns)
        super().update_forward_refs(**localns)
        if hasattr(cls, "_original_cls"):
            cls._original_cls.update_forward_refs(**localns)

    @classmethod
    def _resolve_submodel_fields(cls, registry: dict = None):
        """
        Replace the original field type into the definition of the field
        by the one from the registry
        """
        registry = registry if registry else odoo_pydantic_registry.get()
        for field in cls.__fields__.values():
            cls._resolve_submodel_field(field, registry)

    @classmethod
    def _get_assembled_cls(cls, registry: dict = None) -> ModelType:
        if getattr(cls, "_is_aggregated_class", False):
            return cls
        registry = registry if registry else odoo_pydantic_registry.get()
        return registry[cls.__xreg_name__]

    @classmethod
    def _resolve_submodel_field(cls, field: ModelField, registry: dict):
        if issubclass(field.type_, BaseModel):
            field.type_ = field.type_._get_assembled_cls(registry=registry)
            field.prepare()
        if field.sub_fields:
            for sub_f in field.sub_fields:
                cls._resolve_submodel_field(sub_f, registry)

    @classmethod
    def __register__(cls):
        """Register the class into the list of classes defined by the module"""
        if "tests" not in cls.__module__.split(":"):
            module = utils._get_addon_name(cls.__module__)
            if module not in cls._pydantic_classes_by_module:
                cls._pydantic_classes_by_module[module] = []
            cls._pydantic_classes_by_module[module].append(cls)


_is_base_model_class_defined = True
