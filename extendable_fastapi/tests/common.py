# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from odoo.addons.extendable.tests.common import ExtendableMixin
from odoo.addons.fastapi.tests.common import (
    FastAPITransactionCase as BaseFastAPITransactionCase,
)


class FastAPITransactionCase(BaseFastAPITransactionCase, ExtendableMixin):
    """Base class for FastAPI tests using extendable classes."""

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.init_extendable_registry()
        cls.addClassCleanup(cls.reset_extendable_registry)
