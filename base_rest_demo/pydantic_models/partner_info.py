# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import pydantic

from .country_info import CountryInfo
from .partner_short_info import PartnerShortInfo
from .state_info import StateInfo


class PartnerInfo(PartnerShortInfo):

    street: str
    street2: str = None
    zip_code: str = pydantic.Field(..., alias="zip")
    city: str
    phone: str = None
    state: StateInfo = pydantic.Field(..., alias="state_id")
    country: CountryInfo = pydantic.Field(..., alias="country_id")
    is_company: bool = None
