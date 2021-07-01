:code:`ModelSerializer` class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The :code:`ModelSerializer` class inherits from the :code:`Datamodel` class and adds functionalities. Therefore any
class inheriting from :code:`ModelSerializer` can be used the exact same way as any other :code:`Datamodel`.

Basic example::

    from odoo.addons.model_serializer.core import ModelSerializer

    class PartnerInfo(ModelSerializer):
        _name = "partner.info"
        _model = "res.partner"
        _model_fields = ["id", "name", "country_id"]
