from extendable_pydantic import StrictExtendableBaseModel


class UserScUpdate(StrictExtendableBaseModel, extra="ignore"):
    """
    used to update customer details
    """

    name: str | None = None
    mobile: str | None = None
    opt_in: bool | None = None
    lang_id: int | None = None

    def to_user_vals(self) -> dict:
        fields = self._get_user_update_fields()
        values = self.model_dump(exclude_unset=True)
        values = {f: values[f] for f in fields if f in values}
        return values

    def _get_user_update_fields(self):
        return [
            "name",
            "phone",
            "mobile",
        ]


class UserSc(StrictExtendableBaseModel):
    """
    used to get customer details
    """

    email: str
    name: str | None = None
    phone: str | None = None
    mobile: str | None = None

    @classmethod
    def from_res_user(cls, odoo_rec):
        return cls.model_construct(
            email=odoo_rec.login or None,
            name=odoo_rec.name or None,
            phone=odoo_rec.phone or None,
            mobile=odoo_rec.mobile or None,
        )
