To define your own datamodel you just need to create a class that inherits from
``odoo.addons.datamodel.core.Datamodel``

.. code-block:: python

    from marshmallow import fields

    from odoo.addons.base_rest import restapi
    from odoo.addons.component.core import Component
    from odoo.addons.datamodel.core import Datamodel


    class PartnerShortInfo(Datamodel):
        _name = "partner.short.info"

        id = fields.Integer(required=True, allow_none=False)
        name = fields.String(required=True, allow_none=False)

    class PartnerInfo(Datamodel):
        _name = "partner.info"
        _inherit = "partner.short.info"

        street = fields.String(required=True, allow_none=False)
        street2 = fields.String(required=False, allow_none=True)
        zip_code = fields.String(required=True, allow_none=False)
        city = fields.String(required=True, allow_none=False)
        phone = fields.String(required=False, allow_none=True)
        is_componay = fields.Boolean(required=False, allow_none=False)


As for odoo models, you can extend the `base` datamodel by inheriting of `base`.

.. code-block:: python

    class Base(Datamodel):
        _inherit = "base"

        def _my_method(self):
            pass

Datamodels are available through the `datamodels` registry provided by the Odoo's environment.

.. code-block:: python

    class ResPartner(Model):
        _inherit = "res.partner"

        def _to_partner_info(self):
            PartnerInfo = self.env.datamodels["partner.info"]
            partner_info = PartnerInfo(partial=True)
            partner_info.id = partner.id
            partner_info.name = partner.name
            partner_info.street = partner.street
            partner_info.street2 = partner.street2
            partner_info.zip_code = partner.zip
            partner_info.city = partner.city
            partner_info.phone = partner.phone
            partner_info.is_company = partner.is_company
            return partner_info

The Odoo's environment is also available into the datamodel instance.

.. code-block:: python

    class MyDataModel(Datamodel):
        _name = "my.data.model"

        def _my_method(self):
            partners = self.env["res.partner"].search([])

.. warning::

  The `env` property into a Datamodel instance is mutable. IOW, you can't rely
  on information (context, user) provided by the environment. The `env` property
  is a helper property that give you access to the odoo's registry and must
  be use with caution.
