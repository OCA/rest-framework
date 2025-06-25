# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    endpoint_id_column = openupgrade.get_legacy_name("fastapi_endpoint_id")
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE api_log SET
        collection_id=%(endpoint_id_column)s,
        collection_model='fastapi.endpoint',
        collection_ref='fastapi.endpoint,' || %(endpoint_id_column)s
        WHERE %(endpoint_id_column)s IS NOT NULL
        """
        % {
            "endpoint_id_column": endpoint_id_column,
        },
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE api_log
        DROP COLUMN %(endpoint_id_column)s
        """
        % {
            "endpoint_id_column": endpoint_id_column,
        },
    )
