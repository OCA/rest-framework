# Copyright 2017 Camptocamp SA
# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import copy
from contextlib import contextmanager

import odoo
from odoo import api
from odoo.tests import common

from ..core import (
    DatamodelRegistry,
    MetaDatamodel,
    _datamodel_databases,
    _get_addon_name,
)


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


class DatamodelMixin(object):
    @classmethod
    def setUpDatamodel(cls):
        with new_rollbacked_env() as env:
            builder = env["datamodel.builder"]
            # build the datamodels of every installed addons
            datamodel_registry = builder._init_global_registry()
            cls._datamodels_registry = datamodel_registry
            # ensure that we load only the datamodels of the 'installed'
            # modules, not 'to install', which means we load only the
            # dependencies of the tested addons, not the siblings or
            # chilren addons
            builder.build_registry(datamodel_registry, states=("installed",))
            # build the datamodels of the current tested addon
            current_addon = _get_addon_name(cls.__module__)
            env["datamodel.builder"].load_datamodels(current_addon)

    # pylint: disable=W8106
    def setUp(self):
        # should be ready only during tests, never during installation
        # of addons
        self._datamodels_registry.ready = True

        @self.addCleanup
        def notready():
            self._datamodels_registry.ready = False


class TransactionDatamodelCase(common.TransactionCase, DatamodelMixin):
    """A TransactionCase that loads all the datamodels

    It it used like an usual Odoo's TransactionCase, but it ensures
    that all the datamodels of the current addon and its dependencies
    are loaded.

    """

    @classmethod
    def setUpClass(cls):
        super(TransactionDatamodelCase, cls).setUpClass()
        cls.setUpDatamodel()

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not call
        # super)
        common.TransactionCase.setUp(self)
        DatamodelMixin.setUp(self)


class SavepointDatamodelCase(common.SavepointCase, DatamodelMixin):
    """A SavepointCase that loads all the datamodels

    It is used like an usual Odoo's SavepointCase, but it ensures
    that all the datamodels of the current addon and its dependencies
    are loaded.

    """

    @classmethod
    def setUpClass(cls):
        super(SavepointDatamodelCase, cls).setUpClass()
        cls.setUpDatamodel()

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.SavepointCase does not call
        # super)
        common.SavepointCase.setUp(self)
        DatamodelMixin.setUp(self)


class DatamodelRegistryCase(
    common.TreeCase, common.MetaCase("DummyCase", (object,), {})
):
    """This test case can be used as a base for writings tests on datamodels

    This test case is meant to test datamodels in a special datamodel registry,
    where you want to have maximum control on which datamodels are loaded
    or not, or when you want to create additional datamodels in your tests.

    If you only want to *use* the datamodels of the tested addon in your tests,
    then consider using one of:

    * :class:`TransactionDatamodelCase`
    * :class:`SavepointDatamodelCase`

    This test case creates a special
    :class:`odoo.addons.datamodel.core.DatamodelRegistry` for the purpose of
    the tests. By default, it loads all the datamodels of the dependencies, but
    not the datamodels of the current addon (which you have to handle
    manually). In your tests, you can add more datamodels in 2 manners.

    All the datamodels of an Odoo module::

        self._load_module_datamodels('connector')

    Only specific datamodels::

        self._build_datamodels(MyDatamodel1, MyDatamodel2)

    Note: for the lookups of the datamodels, the default datamodel
    registry is a global registry for the database. Here, you will
    need to explicitly pass ``self.datamodel_registry`` in the
    """

    def setUp(self):
        super(DatamodelRegistryCase, self).setUp()

        # keep the original classes registered by the metaclass
        # so we'll restore them at the end of the tests, it avoid
        # to pollute it with Stub / Test datamodels
        self._original_datamodels = copy.deepcopy(MetaDatamodel._modules_datamodels)

        # it will be our temporary datamodel registry for our test session
        self.datamodel_registry = DatamodelRegistry()

        # it builds the 'final datamodel' for every datamodel of the
        # 'datamodel' addon and push them in the datamodel registry
        self.datamodel_registry.load_datamodels("datamodel")
        # build the datamodels of every installed addons already installed
        # but the current addon (when running with pytest/nosetest, we
        # simulate the --test-enable behavior by excluding the current addon
        # which is in 'to install' / 'to upgrade' with --test-enable).
        current_addon = _get_addon_name(self.__module__)

        registry = odoo.registry(common.get_db_name())
        uid = odoo.SUPERUSER_ID
        cr = registry.cursor()
        env = api.Environment(cr, uid, {})
        env["datamodel.builder"].build_registry(
            self.datamodel_registry,
            states=("installed",),
            exclude_addons=[current_addon],
        )
        self.env = env
        _datamodel_databases[self.env.cr.dbname] = self.datamodel_registry

        @self.addCleanup
        def _close_and_roolback():
            cr.rollback()  # we shouldn't have to commit anything
            cr.close()

        # Fake that we are ready to work with the registry
        # normally, it is set to True and the end of the build
        # of the datamodels. Here, we'll add datamodels later in
        # the datamodels registry, but we don't mind for the tests.
        self.datamodel_registry.ready = True

    def tearDown(self):
        super(DatamodelRegistryCase, self).tearDown()
        # restore the original metaclass' classes
        MetaDatamodel._modules_datamodels = self._original_datamodels

    def _load_module_datamodels(self, module):
        self.datamodel_registry.load_datamodels(module)

    def _build_datamodels(self, *classes):
        for cls in classes:
            cls._build_datamodel(self.datamodel_registry)


class TransactionDatamodelRegistryCase(common.TransactionCase, DatamodelRegistryCase):
    """ Adds Odoo Transaction in the base Datamodel TestCase """

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.TransactionCase does not use
        # super)
        common.TransactionCase.setUp(self)
        DatamodelRegistryCase.setUp(self)
        self.collection = self.env["collection.base"]

    def teardown(self):
        common.TransactionCase.tearDown(self)
        DatamodelRegistryCase.tearDown(self)


class SavepointDatamodelRegistryCase(common.SavepointCase, DatamodelRegistryCase):
    """ Adds Odoo Transaction with Savepoint in the base Datamodel TestCase """

    # pylint: disable=W8106
    def setUp(self):
        # resolve an inheritance issue (common.SavepointCase does not use
        # super)
        common.SavepointCase.setUp(self)
        DatamodelRegistryCase.setUp(self)
        self.collection = self.env["collection.base"]

    def teardown(self):
        common.SavepointCase.tearDown(self)
        DatamodelRegistryCase.tearDown(self)
