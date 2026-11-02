# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from contextlib import contextmanager

from odoo import SUPERUSER_ID, api
from odoo.modules.registry import Registry
from odoo.tests import common

from extendable import context, main


def _get_addon_name(full_name: str) -> str:
    # The (Odoo) module name can be in the ``odoo.addons`` namespace
    # or not. For instance, module ``sale`` can be imported as
    # ``odoo.addons.sale`` (the right way) or ``sale`` (for backward
    # compatibility).
    module_parts = full_name.split(".")
    if len(module_parts) > 2 and module_parts[:2] == ["odoo", "addons"]:
        addon_name = full_name.split(".")[2]
    else:
        addon_name = full_name.split(".")[0]
    return addon_name


@contextmanager
def new_rollbacked_env():
    registry = Registry(common.get_db_name())
    uid = SUPERUSER_ID
    cr = registry.cursor()
    try:
        yield api.Environment(cr, uid, {})
    finally:
        cr.rollback()  # we shouldn't have to commit anything
        cr.close()


class ExtendableMixin:
    @classmethod
    def init_extendable_registry(cls):
        with new_rollbacked_env() as env:
            builder = env["extendable.registry.loader"]
            # build the extendable classes of every installed addons
            extendable_registry = builder._init_global_registry()
            cls._extendable_registry = extendable_registry
            # ensure that we load only the extendable classes of the 'installed'
            # modules, not 'to install', which means we load only the
            # dependencies of the tested addons, not the siblings or
            # children addons
            builder.build_registry(extendable_registry, states=("installed",))
            # build the extendable classes of the current tested addon
            current_addon = _get_addon_name(cls.__module__)
            extendable_registry.init_registry([f"odoo.addons.{current_addon}.*"])
            cls.token = context.extendable_registry.set(cls._extendable_registry)

    @classmethod
    def backup_extendable_registry(cls):
        # Store the current extendable classes
        cls._initial_extendable_class_defs_by_module = (
            main._extendable_class_defs_by_module
        )
        # Use a copy of the current extendable classes
        main._extendable_class_defs_by_module = dict(
            cls._initial_extendable_class_defs_by_module
        )

    @classmethod
    def restore_extendable_registry(cls):
        # Restore the initial extendable classes
        main._extendable_class_defs_by_module = (
            cls._initial_extendable_class_defs_by_module
        )

    @classmethod
    def reset_extendable_registry(cls):
        context.extendable_registry.reset(cls.token)
