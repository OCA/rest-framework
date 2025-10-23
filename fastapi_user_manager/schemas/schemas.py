from extendable_pydantic import StrictExtendableBaseModel


class UserScUpdate(StrictExtendableBaseModel, extra="ignore"):
    """
    used to update user details
    """

    login: str | None = None
    misc: dict | None = None

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
            "misc",
        ]


class UserSc(StrictExtendableBaseModel):
    """
    used to get user details
    """

    login: str
    misc: dict | None = None

    # @classmethod
    # def from_res_user(cls, odoo_rec):
    #     return cls.model_construct(
    #         email=odoo_rec.login or None,
    #         name=odoo_rec.name or None,
    #         phone=odoo_rec.phone or None,
    #         mobile=odoo_rec.mobile or None,
    #         compny=odoo_rec.company_id.name or None,
    #         role=odoo_rec.role_id.name or None,
    #     )


class UserScDel(StrictExtendableBaseModel):
    email: str | None = None
    name: str | None = None
    login: str
