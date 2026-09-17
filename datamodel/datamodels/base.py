# Copyright 2019 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html)

from ..core import Datamodel


class BaseDatamodel(Datamodel):
    """This is the base datamodel for every datamodel

    It is implicitely inherited by all datamodels.

    All your base are belong to us
    """

    _name = "base"
