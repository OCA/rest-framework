import datetime

from odoo import fields
from odoo.tests import TransactionCase

from pydantic import Field

from ..utils import PydanticOdooBaseModel as PydanticOrmBaseModel


class OdooBaseModel(PydanticOrmBaseModel):
    id: int


class PartnerModel(OdooBaseModel):
    name: str


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


class CurrencyRateModel(OdooBaseModel):
    name: datetime.date | None = None
    rate: float


class CommonPydanticCase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_demo = cls.env.ref("base.user_demo")
        cls.user_demo.action_id = False
        cls.user_demo.signature = False
        cls.user_demo.share = False
        cls.currency_eur = cls.env.ref("base.USD")
        cls.currency_rate = cls.env.ref("base.rateUSD")


class TestGenericOdooGetterPydanticV2Case(CommonPydanticCase):
    def test_user_model_serialization(self):
        self.currency_rate.name = None  # name is a date field
        self.assertEqual(
            CurrencyRateModel.model_validate(
                self.currency_rate, from_attributes=True
            ).model_dump(),
            {
                "id": self.currency_rate.id,
                "name": None,
                "rate": self.currency_rate.rate,
            },
        )

    def test_user_model_serialization_date(self):
        self.currency_rate.name = fields.Date.today()  # name is a date field
        self.assertEqual(
            CurrencyRateModel.model_validate(self.currency_rate).name,
            self.currency_rate.name,
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

    def test_not_an_odoo_record(self):
        user = UserDetailsModel(
            id=666,
            partner_id={"id": 66, "name": "test"},
            groups_id=[{"id": 33, "name": "group 1"}],
            action_id={"id": 55},
            signature=None,
            active=True,
            share=False,
            write_date=fields.Datetime.now(),
        )
        self.assertEqual(
            UserDetailsModel.model_validate(user).model_dump(), user.model_dump()
        )
