# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

_logger = logging.getLogger(__name__)


def post_init_hook(cr, version):
    """Preserve log entries from old implementation in shopfloor."""
    cr.execute("SELECT 1 FROM pg_class WHERE relname = 'shopfloor_log'")
    if not cr.fetchone():
        # shopfloor_log was already removed
        return

    _logger.info("Copy shopfloor.log records to rest.log")
    cr.execute(
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
    cr.execute("""DELETE FROM shopfloor_log""")
