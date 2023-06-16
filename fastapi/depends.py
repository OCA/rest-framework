# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import warnings

warnings.warn(
    "The 'depends' package is deprecated. Please use 'dependencies' instead.",
    DeprecationWarning,
    stacklevel=2,
)

from .dependencies import *  # noqa: F403, F401, E402
