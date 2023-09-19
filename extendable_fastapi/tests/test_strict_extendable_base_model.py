import warnings
from datetime import date

from extendable_pydantic import ExtendableBaseModel

from pydantic import ValidationError

from ..schemas import StrictExtendableBaseModel
from .common import FastAPITransactionCase


class TestStrictExtendableBaseModel(FastAPITransactionCase):
    class Model(ExtendableBaseModel):
        x: int
        d: date | None

    class StrictModel(StrictExtendableBaseModel):
        x: int
        d: date | None

    def test_Model_revalidate_instance_never(self):
        # Missing required fields but no re-validation
        m = self.Model.model_construct()
        self.assertEqual(m.model_validate(m).model_dump(), {})

    def test_StrictModel_revalidate_instance_always(self):
        # Missing required fields and always revalidate
        m = self.StrictModel.model_construct()
        with self.assertRaises(ValidationError):
            m.model_validate(m)

    def test_Model_validate_assignment_false(self):
        # Wrong assignment but no re-validation at assignment
        m = self.Model(x=1, d=None)
        m.x = "TEST"
        with warnings.catch_warnings():
            # Disable 'Expected `int` but got `str`' warning
            warnings.simplefilter("ignore")
            self.assertEqual(m.model_dump(), {"x": "TEST", "d": None})

    def test_StrictModel_validate_assignment_true(self):
        # Wrong assignment and validation at assignment
        m = self.StrictModel.model_construct()
        m.x = 1  # Validate only this field -> OK even if m.d is not set
        with self.assertRaises(ValidationError):
            m.x = "TEST"

    def test_Model_extra_ignored(self):
        # Ignore extra fields
        m = self.Model(x=1, z=3, d=None)
        self.assertEqual(m.model_dump(), {"x": 1, "d": None})

    def test_StrictModel_extra_forbidden(self):
        # Forbid extra fields
        with self.assertRaises(ValidationError):
            self.StrictModel(x=1, z=3, d=None)

    def test_StrictModel_strict_false(self):
        # Coerce str->date is allowed to enable coercion from JSON
        # by FastAPI
        m = self.StrictModel(x=1, d=None)
        m.d = "2023-01-01"
        self.assertTrue(m.model_validate(m))
