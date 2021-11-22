To define your own pydantic model you just need to create a class that inherits from
``odoo.addons.pydantic.models.BaseModel`` or a subclass of.

.. code-block:: python

    from odoo.addons.pydantic.models import BaseModel
    from pydantic import Field


    class PartnerShortInfo(BaseModel):
        id: str
        name: str


    class PartnerInfo(BaseModel):
        street: str
        street2: str = None
        zip_code: str = None
        city: str
        phone: str = None
        is_componay : bool = Field(None)


In the preceding code, 2 new models are created, one for each class. If you
want to extend an existing model, you must pass the extended pydantic model
trough the `extends` parameter on class declaration.

.. code-block:: python

    class Coordinate(models.BaseModel):
        lat = 0.1
        lng = 10.1

    class PartnerInfoWithCoordintate(PartnerInfo, extends=PartnerInfo):
        coordinate: Coordinate = None

`PartnerInfoWithCoordintate` extends `PartnerInfo`. IOW, Base class are now the
same and define the same fields and methods. They can be used indifferently into
the code. All the logic will be provided by the aggregated class.

.. code-block:: python

    partner1 = PartnerInfo.construct()
    partner2 = PartnerInfoWithCoordintate.construct()

    assert partner1.__class__ == partner2.__class__
    assert PartnerInfo.schema() == PartnerInfoWithCoordinate.schema()

.. note::

    Since validation occurs on instance creation, it's important to avoid to
    create an instance of a Pydantic class by usign the normal instance
    constructor `partner = PartnerInfo(..)`. In such a case, if the class is
    extended by an other addon and a required field is added, this code will
    no more work. It's therefore a good practice to use the `construct()` class
    method to create a pydantic instance.

.. caution::

    Adding required fields to an existing data structure into an extension
    addon violates the `Liskov substitution principle`_ and should generally
    be avoided. This is certainly forbidden in requests data structures.
    When extending response  data structures this could be useful to document
    new fields that are guaranteed to be present when extension addons are
    installed.

In contrast to Odoo, access to a Pydantic class is not done through a specific
registry. To use a Pydantic class, you just have to import it in your module
and write your code like in any other python application.

.. code-block:: python

    from odoo.addons.my_addons.datamodels import PartnerInfo
    from odoo import models

    class ResPartner(models.Basemodel):
       _inherit = "res.partner"

       def to_json(self):
           return [i._to_partner_info().json() for i in self]

       def _to_partner_info(self):
           self.ensure_one()
           pInfo = PartnerInfo.construct(id=self.id, name=self.name, street=self.street, city=self.city)
           return pInfo


To support pydantic models that map to Odoo models, Pydantic model instances can
be created from arbitrary odoo model instances by mapping fields from odoo
models to fields defined by the pydantic model. To ease the mapping, the addon
provide a utility class `odoo.addons.pydantic.utils.GenericOdooGetter`.

.. code-block:: python

    import pydantic
    from odoo.addons.pydantic import models, utils

    class Group(models.BaseModel):
        name: str

        class Config:
            orm_mode = True
            getter_dict = utils.GenericOdooGetter

    class UserInfo(models.BaseModel):
        name: str
        groups: List[Group] = pydantic.Field(alias="groups_id")

        class Config:
            orm_mode = True
            getter_dict = utils.GenericOdooGetter

    user = self.env.user
    user_info = UserInfo.from_orm(user)

See the official `Pydantic documentation`_ to discover all the available functionalities.

.. _`Liskov substitution principle`: https://en.wikipedia.org/wiki/Liskov_substitution_principle
.. _`Pydantic documentation`: https://pydantic-docs.helpmanual.io/
