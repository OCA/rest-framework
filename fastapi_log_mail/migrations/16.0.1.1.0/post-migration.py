# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    template_id_column = openupgrade.get_legacy_name(
        "fastapi_log_mail_template_id",
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE fastapi_endpoint SET
        api_log_mail_exception_template_id=%(template_id_column)s
        WHERE %(template_id_column)s IS NOT NULL
        """
        % {
            "template_id_column": template_id_column,
        },
    )
    openupgrade.logged_query(
        env.cr,
        """
        ALTER TABLE fastapi_endpoint
        DROP COLUMN %(template_id_column)s
        """
        % {
            "template_id_column": template_id_column,
        },
    )
