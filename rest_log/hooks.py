# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(cr):
    """On first install copy recods from shopfloor_log table if available.

    """
    cr.execute("SELECT 1 FROM pg_class WHERE relname = 'rest_log'")
    if cr.fetchone():
        # rest_log was already installed
        return
    cr.execute("SELECT 1 FROM pg_class WHERE relname = 'shopfloor_log'")
    if not cr.fetchone():
        # shopfloor_log was already removed
        return
    _logger.info("Copy shopfloor.log records to rest.log")
    cr.execute("CREATE TABLE rest_log AS TABLE shopfloor_log")
