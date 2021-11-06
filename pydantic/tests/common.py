# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

import collections
from contextlib import contextmanager

import odoo
from odoo import api
from odoo.tests import common

from .. import registry, utils
from ..models import BaseModel


@contextmanager
def new_rollbacked_env():
    registry = odoo.registry(common.get_db_name())
    uid = odoo.SUPERUSER_ID
    cr = registry.cursor()
    try:
        yield api.Environment(cr, uid, {})
    finally:
        cr.rollback()  # we shouldn't have to commit anything
        cr.close()


class PydanticMixin(object):
    @classmethod
    def setUpPydantic(cls):
        with new_rollbacked_env() as env:
            builder = env["pydantic.classes.builder"]
            # build the pydantic classes of every installed addons
            pydantic_registry = builder._init_global_registry()
            cls._pydantics_registry = pydantic_registry
            # ensure that we load only the pydantic classes of the 'installed'
            # modules, not 'to install', which means we load only the
            # dependencies of the tested addons, not the siblings or
            # chilren addons
            builder.build_registry(pydantic_registry, states=("installed",))
            # build the pydantic classes of the current tested addon
            current_addon = utils._get_addon_name(cls.__module__)
            builder.build_classes(current_addon, pydantic_registry)

    # pylint: disable=W8106
    def setUp(self):
        # should be ready only during tests, never during installation
        # of addons
        self._pydantics_registry.ready = True

        @self.addCleanup
        def notready():
            self._pydantics_registry.ready = False


class TransactionPydanticCase(common.TransactionCase, PydanticMixin):
    """A TransactionCase that loads all the pydantic classes

    It it used like an usual Odoo's TransactionCase, but it ensures
    that all the pydantic classes of the current addon and its dependencies
    are loaded.

    """

    @classmethod
    def setUpClass(cls):
        super(TransactionPydanticCase, cls).setUpClass()
        cls.setUpPydantic()

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not call
        # super)
        common.TransactionCase.setUp(self)
        PydanticMixin.setUp(self)


class SavepointPydanticCase(common.SavepointCase, PydanticMixin):
    """A SavepointCase that loads all the pydantic classes

    It is used like an usual Odoo's SavepointCase, but it ensures
    that all the pydantic classes of the current addon and its dependencies
    are loaded.

    """

    @classmethod
    def setUpClass(cls):
        super(SavepointPydanticCase, cls).setUpClass()
        cls.setUpPydantic()

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.SavepointCase does not call
        # super)
        common.SavepointCase.setUp(self)
        PydanticMixin.setUp(self)


class PydanticRegistryCase(
    common.TreeCase, common.MetaCase("DummyCase", (object,), {})
):
    """This test case can be used as a base for writings tests on pydantic classes

    This test case is meant to test pydantic classes in a special pydantic registry,
    where you want to have maximum control on which pydantic classes are loaded
    or not, or when you want to create additional pydantic classes in your tests.

    If you only want to *use* the pydantic classes of the tested addon in your tests,
    then consider using one of:

    * :class:`TransactionPydanticCase`
    * :class:`SavepointPydanticCase`

    This test case creates a special
    :class:`odoo.addons.pydantic.registry.PydanticClassesRegistry` for the purpose of
    the tests. By default, it loads all the pydantic classes of the dependencies, but
    not the pydantic classes of the current addon (which you have to handle
    manually). In your tests, you can add more pydantic classes in 2 manners.

    All the pydantic classes of an Odoo module::

        self._load_module_pydantics('my_addon')

    Only specific pydantic classes::

        self._build_pydantic_classes(MyPydantic1, MyPydantic2)

    Note: for the lookups of the pydantic classes, the default pydantic
    registry is a global registry for the database. Here, you will
    need to explicitly pass ``self.pydantic_registry``
    """

    def setUp(self):
        super(PydanticRegistryCase, self).setUp()

        # keep the original classes registered by the annotation
        # so we'll restore them at the end of the tests, it avoid
        # to pollute it with Stub / Test pydantic classes
        self.backup_registry()
        # it will be our temporary pydantic registry for our test session
        self.pydantic_registry = registry.PydanticClassesRegistry()

        # it builds the 'final pydantic' for every pydantic of the
        # 'pydantic' addon and push them in the pydantic registry
        self.pydantic_registry.load_pydantic_classes("pydantic")
        # build the pydantic classes of every installed addons already installed
        # but the current addon (when running with pytest/nosetest, we
        # simulate the --test-enable behavior by excluding the current addon
        # which is in 'to install' / 'to upgrade' with --test-enable).
        current_addon = utils._get_addon_name(self.__module__)

        odoo_registry = odoo.registry(common.get_db_name())
        uid = odoo.SUPERUSER_ID
        cr = odoo_registry.cursor()
        env = api.Environment(cr, uid, {})
        env["pydantic.classes.builder"].build_registry(
            self.pydantic_registry,
            states=("installed",),
            exclude_addons=[current_addon],
        )
        self.env = env
        registry._pydantic_classes_databases[
            self.env.cr.dbname
        ] = self.pydantic_registry

        @self.addCleanup
        def _close_and_roolback():
            cr.rollback()  # we shouldn't have to commit anything
            cr.close()

        # Fake that we are ready to work with the registry
        # normally, it is set to True and the end of the build
        # of the pydantic classes. Here, we'll add pydantic classes later in
        # the pydantic classes registry, but we don't mind for the tests.
        self.pydantic_registry.ready = True

    def tearDown(self):
        super(PydanticRegistryCase, self).tearDown()
        self.restore_registry()

    def _load_module_pydantics(self, module):
        self.pydantic_registry.load_pydantics(module)

    def _build_pydantic_classes(self, *classes):
        for cls in classes:
            self.pydantic_registry.load_pydantic_class_def(cls)
        self.pydantic_registry.build_pydantic_classes()
        self.pydantic_registry.update_forward_refs()

    def backup_registry(self):
        self._original_classes_by_module = collections.defaultdict(list)
        for k, v in BaseModel._pydantic_classes_by_module.items():
            self._original_classes_by_module[k] = [i for i in v]
        self._original_registry = registry._pydantic_classes_databases.get(
            common.get_db_name()
        )

    def restore_registry(self):
        BaseModel._pydantic_classes_by_module = self._original_classes_by_module
        registry._pydantic_classes_databases[
            common.get_db_name()
        ] = self._original_registry


class TransactionPydanticRegistryCase(common.TransactionCase, PydanticRegistryCase):
    """ Adds Odoo Transaction in the base Pydantic TestCase """

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not use
        # super)
        common.TransactionCase.setUp(self)
        PydanticRegistryCase.setUp(self)

    def teardown(self):
        common.TransactionCase.tearDown(self)
        PydanticRegistryCase.tearDown(self)


class SavepointPydanticRegistryCase(common.SavepointCase, PydanticRegistryCase):
    """ Adds Odoo Transaction with Savepoint in the base Pydantic TestCase """

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.SavepointCase does not use
        # super)
        common.SavepointCase.setUp(self)
        PydanticRegistryCase.setUp(self)

    def teardown(self):
        common.SavepointCase.tearDown(self)
        PydanticRegistryCase.tearDown(self)
