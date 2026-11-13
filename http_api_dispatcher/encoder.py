# Copyright 2018 ACSONE SA/NV
# Copyright 2026 Camptocamp SA
# @author: Simone Orsi <simone.orsi@camptocamp.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
"""JSON encoding of results.

`JSONEncoder` is taken from `base_rest.http` (OCA/rest-framework).
"""

import datetime
import decimal
import json


class JSONEncoder(json.JSONEncoder):
    """Encode dates as ISO strings and decimals as floats."""

    def default(self, obj):  # pylint: disable=method-hidden
        """Encode values not supported by the std encoder."""
        if isinstance(obj, datetime.datetime | datetime.date):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return super().default(obj)


def json_dumps(data, encoder=None):
    """Serialize `data` with given encoder (default: `JSONEncoder`)."""
    return json.dumps(data, cls=encoder or JSONEncoder)
