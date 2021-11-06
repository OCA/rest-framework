To define your own pydantic model you just need to create a class that inherits from
``odoo.addons.pydantic.models.BaseModel``

.. code-block:: python

    from odoo.addons.pydantic.models import BaseModel
    from pydantic import Field


    class PartnerShortInfo(BaseModel):
        _name = "partner.short.info"
        id: str
        name: str


    class PartnerInfo(BaseModel):
        _name = "partner.info"
        _inherit = "partner.short.info"

        street: str
        street2: str = None
        zip_code: str = None
        city: str
        phone: str = None
        is_componay : bool = Field(None)


As for odoo models, you can extend the `base` pydantic model by inheriting of `base`.

.. code-block:: python

    class Base(BaseModel):
        _inherit = "base"

        def _my_method(self):
            pass

Pydantic model classes are available through the `pydantic_registry` registry provided by the Odoo's environment.

To support pydantic models that map to Odoo models, Pydantic model instances can
be created from arbitrary odoo model instances by mapping fields from odoo
models to fields defined by the pydantic model. To ease the mapping,
your pydantic model should inherit from 'odoo_orm_mode'

.. code-block:: python

        class UserInfo(models.BaseModel):
            _name = "user"
            _inherit = "odoo_orm_mode"
            name: str
            groups: List["group"] = pydantic.Field(alias="groups_id")


        class Group(models.BaseModel):
            _name="group"
            _inherit = "odoo_orm_mode"
            name: str

        user = self.env.user
        UserInfoCls = self.env.pydantic_registry["user"]
        user_info = UserInfoCls.from_orm(user)

See the official Pydantic documentation_ to discover all the available functionalities.

.. _documentation: https://pydantic-docs.helpmanual.io/
