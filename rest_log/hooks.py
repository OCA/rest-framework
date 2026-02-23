# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

_logger = logging.getLogger(__name__)


def pre_init_hook(env):
    """On first install copy recods from shopfloor_log table if available."""
    env.cr.execute("SELECT 1 FROM pg_class WHERE relname = 'rest_log'")
    if env.cr.fetchone():
        # rest_log was already installed
        return
    _logger.info("Copy shopfloor.log records to rest.log")
    env.cr.execute(
        """
    INSERT INTO rest_log (
        request_url,
        request_method,
        params,
        headers,
        result,
        error,
        exception_name,
        exception_message,
        state,
        severity,
        create_uid,
        create_date,
        write_uid,
        write_date
    )
    SELECT
        request_url,
        request_method,
        params,
        headers,
        result,
        error,
        exception_name,
        exception_message,
        state,
        severity,
        create_uid,
        create_date,
        write_uid,
        write_date
    FROM shopfloor_log;
    """
    )
    _logger.info("Delete legacy records in shopfloor_log")
    env.cr.execute("""DELETE FROM shopfloor_log""")
