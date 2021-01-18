# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
"""

Fields
=====

Create a single place for all fields defined for datamodels

"""
import logging

from .core import Datamodel

_logger = logging.getLogger(__name__)

try:
    from marshmallow.fields import *  # noqa: F403,F401
    from marshmallow.fields import Nested
except ImportError:
    Nested = object
    _logger.debug("Cannot import 'marshmallow'.")


class NestedModel(Nested):
    def __init__(self, nested, **kwargs):
        self.datamodel_name = nested
        super(NestedModel, self).__init__(None, **kwargs)

    @property
    def schema(self):
        if not self.nested:
            self.nested = self.parent._env.datamodels[
                self.datamodel_name
            ].__schema_class__
            self.nested._env = self.parent._env
        return super(NestedModel, self).schema

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, Datamodel):
            return value
        return super(NestedModel, self)._deserialize(value, attr, data, **kwargs)
