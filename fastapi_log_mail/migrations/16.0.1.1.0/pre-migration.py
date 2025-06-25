# Copyright 2025 Simone Rubino - PyTech
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.copy_columns(
        env.cr,
        {
            "fastapi_endpoint": [
                (
                    "fastapi_log_mail_template_id",
                    None,
                    None,
                ),
            ],
        },
    )
