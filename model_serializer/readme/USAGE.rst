:code:`ModelSerializer` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :code:`ModelSerializer` class inherits from the :code:`Datamodel` class and adds functionalities. Therefore any
class inheriting from :code:`ModelSerializer` can be used the exact same way as any other :code:`Datamodel`.

Basic usage
***********

Here is a basic example::

    from odoo.addons.model_serializer.core import ModelSerializer

    class PartnerInfo(ModelSerializer):
        _name = "partner.info"
        _model = "res.partner"
        _model_fields = ["id", "name", "country_id"]

The result is equivalent to the following :code:`Datamodel` classes::

    from marshmallow import fields

    from odoo.addons.datamodel.core import Datamodel
    from odoo.addons.datamodel.fields import NestedModel


    class PartnerInfo(Datamodel):
        _name = "partner.info"

        id = fields.Integer(required=True, allow_none=False, dump_only=True)
        name = fields.String(required=True, allow_none=False)
        country = NestedModel("_auto_nested_serializer.res.country")


    class _AutoNestedSerializerResCountry(Datamodel):
        _name = "_auto_nested_serializer.res.country"

        id = fields.Integer(required=True, allow_none=False, dump_only=True)
        display_name = fields.String(dump_only=True)


Overriding fields definition
****************************

It is possible to override the default definition of fields as such::

    from odoo.addons.model_serializer.core import ModelSerializer

    class PartnerInfo(ModelSerializer):
        _name = "partner.info"
        _model = "res.partner"
        _model_fields = ["id", "name", "country_id"]

        country_id = NestedModel("country.info")

    class CountryInfo(ModelSerializer):
        _name = "country.info"
        _model = "res.country"
        _model_fields = ["code", "name"]

In this example, we override a :code:`NestedModel` but it works the same for any other field type.

(De)serialization
*****************

:code:`ModelSerializer` does all the heavy-lifting of transforming a :code:`Datamodel` instance into the corresponding
:code:`recordset`, and vice-versa.

To transform a recordset into a (list of) :code:`ModelSerializer` instance(s) (serialization), do the following::

    partner_info = self.env.datamodels["partner.info"].from_recordset(partner)

This will return a single instance; if your recordset contains more than one record, you can get a list of instances
by passing :code:`many=True` to this method.


To transform a :code:`ModelSerializer` instance into a recordset (de-serialization), do the following::

    partner = partner_info.to_recordset()

Unless an existing partner can be found (see below), this method **creates a new record** in the database. You can avoid
that by passing :code:`create=False`, in which case the system will only create them in memory (:code:`NewId` recordset).

In order to determine if the corresponding Odoo record already exists or if a new one should be created, the system
checks by default if the :code:`id` field of the instance corresponds to a database record. This default behavior can be
modified like so::

    class CountryInfo(ModelSerializer):
        _name = "country.info"
        _model = "res.country"
        _model_fields = ["code", "name"]

        def get_odoo_record(self):
            if self.code:
                return self.env[self._model].search([("code", "=", self.code)])
            return super().get_odoo_record()
