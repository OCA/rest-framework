# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""Helpers for API endpoints.

`to_int` is taken from `base_rest.components.service` (OCA/rest-framework).
"""


def to_int(val):
    """Convert to integer values coming as strings or floats.

    JS clients might send numbers as floats
    and query string values are always strings.
    """
    if isinstance(val, int):
        return val
    if val:
        return int(float(val))
    return None
