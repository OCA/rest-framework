# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)
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
            # Get the major parent to avoid error of _env does not exist
            super_parent = None
            parent = self
            while not super_parent:
                if not hasattr(parent, "parent"):
                    super_parent = parent
                    break
                parent = parent.parent
            self.nested = super_parent._env.datamodels[
                self.datamodel_name
            ].__schema_class__
            self.nested._env = super_parent._env
        return super(NestedModel, self).schema

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, Datamodel):
            return value
        return super(NestedModel, self)._deserialize(value, attr, data, **kwargs)
