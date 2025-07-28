import datetime
from unittest import skipIf

from odoo import fields
from odoo.tests import TransactionCase

from pydantic import BaseModel, Field

from ..utils import PYDANTIC_V2

if PYDANTIC_V2:
    from ..utils import PydanticOdooBaseModel as PydanticOrmBaseModel

else:
    from ..utils import GenericOdooGetter

    class PydanticOrmBaseModel(BaseModel):
        class Config:
            orm_mode = True
            getter_dict = GenericOdooGetter


class OdooBaseModel(PydanticOrmBaseModel):
    id: int


class PartnerModel(OdooBaseModel):
    name: str
    date: datetime.date | None = None


class UserFlatModel(OdooBaseModel):
    partner_id: int = Field(title="Partner")


class GroupModel(OdooBaseModel):
    name: str


class UserModel(OdooBaseModel):
    partner: PartnerModel = Field(title="Partner", alias="partner_id")


class UserDetailsModel(UserModel):
    groups: list[GroupModel] = Field(alias="groups_id")
    action_id: OdooBaseModel | None = None
    signature: str | None = None
    active: bool | None = None
    share: bool | None = None
    write_date: datetime.datetime


class CommonPydanticCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        cls.user_demo.action_id = False
        cls.user_demo.signature = False
        cls.user_demo.share = False


@skipIf(PYDANTIC_V2, "Ignore because Pydantic >= 2.0 is installed")
class TestGenericOdooGetterPydanticV1Case(CommonPydanticCase):
    def test_user_model_serialization(self):
        self.user_demo.partner_id.date = None
        self.assertEqual(
            UserModel.from_orm(self.user_demo).dict(),
            {
                "id": self.user_demo.id,
                "partner": {
                    "id": self.user_demo.partner_id.id,
                    "name": self.user_demo.partner_id.name,
                    "date": None,
                },
            },
        )

    def test_user_model_serialization_date(self):
        self.user_demo.partner_id.date = fields.Date.today()
        self.assertEqual(
            UserModel.from_orm(self.user_demo).partner.date,
            self.user_demo.partner_id.date,
        )

    def test_user_model_details_serialization_datetime(self):
        user_demo = self.user_demo.with_context(tz="Asia/Tokyo")
        self.assertEqual(
            UserDetailsModel.from_orm(user_demo).write_date,
            fields.Datetime.context_timestamp(user_demo, user_demo.write_date),
        )
        self.assertNotEqual(
            UserDetailsModel.from_orm(user_demo).write_date.tzinfo,
            fields.Datetime.context_timestamp(
                self.user_demo, user_demo.write_date
            ).tzinfo,
        )

    def test_user_details_model_serialization(self):
        self.assertEqual(
            UserDetailsModel.from_orm(self.user_demo).dict(),
            {
                "id": self.user_demo.id,
                "partner": {
                    "id": self.user_demo.partner_id.id,
                    "name": self.user_demo.partner_id.name,
                    "date": None,
                },
                "groups": [
                    {
                        "id": group.id,
                        "name": group.name,
                    }
                    for group in self.user_demo.groups_id
                ],
                "action_id": None,
                "signature": None,
                "active": True,
                "share": False,
                "write_date": fields.Datetime.context_timestamp(
                    self.user_demo, self.user_demo.write_date
                ),
            },
        )

    def test_user_flat_model_serialization(self):
        self.assertEqual(
            UserFlatModel.from_orm(self.user_demo).dict(),
            {
                "id": self.user_demo.id,
                "partner_id": self.user_demo.partner_id.id,
            },
        )


@skipIf(not PYDANTIC_V2, "Ignore because Pydantic < 2.0 is installed")
class TestGenericOdooGetterPydanticV2Case(CommonPydanticCase):
    def test_user_model_serialization(self):
        self.user_demo.partner_id.date = None
        self.assertEqual(
            UserModel.model_validate(self.user_demo, from_attributes=True).model_dump(),
            {
                "id": self.user_demo.id,
                "partner": {
                    "id": self.user_demo.partner_id.id,
                    "name": self.user_demo.partner_id.name,
                    "date": None,
                },
            },
        )

    def test_user_model_serialization_date(self):
        self.user_demo.partner_id.date = fields.Date.today()
        self.assertEqual(
            UserModel.model_validate(self.user_demo).partner.date,
            self.user_demo.partner_id.date,
        )

    def test_user_model_details_serialization_datetime(self):
        user_demo = self.user_demo.with_context(tz="Asia/Tokyo")
        self.assertEqual(
            UserDetailsModel.model_validate(user_demo).write_date,
            fields.Datetime.context_timestamp(user_demo, user_demo.write_date),
        )
        self.assertNotEqual(
            UserDetailsModel.model_validate(user_demo).write_date.tzinfo,
            fields.Datetime.context_timestamp(
                self.user_demo, user_demo.write_date
            ).tzinfo,
        )

    def test_user_details_model_serialization(self):
        self.assertEqual(
            UserDetailsModel.model_validate(self.user_demo).model_dump(),
            {
                "id": self.user_demo.id,
                "partner": {
                    "id": self.user_demo.partner_id.id,
                    "name": self.user_demo.partner_id.name,
                    "date": None,
                },
                "groups": [
                    {
                        "id": group.id,
                        "name": group.name,
                    }
                    for group in self.user_demo.groups_id
                ],
                "action_id": None,
                "signature": None,
                "active": True,
                "share": False,
                "write_date": fields.Datetime.context_timestamp(
                    self.user_demo, self.user_demo.write_date
                ),
            },
        )

    def test_user_flat_model_serialization(self):
        self.assertEqual(
            UserFlatModel.model_validate(self.user_demo).model_dump(),
            {
                "id": self.user_demo.id,
                "partner_id": self.user_demo.partner_id.id,
            },
        )
