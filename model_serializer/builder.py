from odoo import models

from odoo.addons.datamodel.core import MetaDatamodel, _datamodel_databases

from .core import ModelSerializer


class DatamodelBuilder(models.AbstractModel):
    _inherit = "datamodel.builder"

    def load_datamodels(self, module, datamodels_registry=None):
        super().load_datamodels(module, datamodels_registry=datamodels_registry)
        datamodels_registry = (
            datamodels_registry or _datamodel_databases[self.env.cr.dbname]
        )
        for datamodel_class in MetaDatamodel._modules_datamodels[module]:
            self._extend_model_serializer(datamodel_class, datamodels_registry)

    def _extend_model_serializer(self, datamodel_class, registry):
        """Extend the datamodel_class with the fields declared in `_model_fields`"""
        if issubclass(datamodel_class, ModelSerializer):
            new_class = datamodel_class._extend_from_odoo_model(registry, self.env)
            new_class._build_datamodel(registry)
