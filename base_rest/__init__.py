import logging
from . import models
from . import components
from . import http

logging.getLogger(__file__).warning(
    "base_rest is deprecated and not fully supported anymore on Odoo 16. "
    "Please migrate to the FastAPI migration module. "
    "See https://github.com/OCA/rest-framework/pull/291.",
)
