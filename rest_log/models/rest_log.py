# -*- coding: utf-8 -*-
# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging
from datetime import datetime, timedelta

from odoo import api, fields, models, tools

_logger = logging.getLogger(__name__)


class RESTLog(models.Model):
    _name = "rest.log"
    _description = "REST API Logging"
    _order = "id desc"

    DEFAULT_RETENTION = 30  # days
    EXCEPTION_SEVERITY_MAPPING = {
        "odoo.exceptions.UserError": "functional",
        "odoo.exceptions.ValidationError": "functional",
        # something broken somewhere
        "ValueError": "severe",
        "AttributeError": "severe",
        "UnboundLocalError": "severe",
    }

    collection = fields.Char(index=True)
    request_url = fields.Char(readonly=True, string="Request URL")
    request_method = fields.Char(readonly=True)
    params = fields.Text(readonly=True)
    # TODO: make these fields serialized and use a computed field for displaying
    headers = fields.Text(readonly=True)
    result = fields.Text(readonly=True)
    error = fields.Text(readonly=True)
    exception_name = fields.Char(readonly=True, string="Exception")
    exception_message = fields.Text(readonly=True)
    state = fields.Selection(
        selection=[("success", "Success"), ("failed", "Failed")], readonly=True
    )
    severity = fields.Selection(
        selection=[
            ("functional", "Functional"),
            ("warning", "Warning"),
            ("severe", "Severe"),
        ],
        compute="_compute_severity",
        store=True,
        # Grant specific override services' dispatch_exception override
        # or via UI: user can classify errors as preferred on demand
        # (maybe using mass_edit)
        readonly=False,
    )

    @api.depends("state", "exception_name", "error")
    def _compute_severity(self):
        for rec in self:
            rec.severity = rec.severity or rec._get_severity()

    def _get_severity(self):
        if not self.exception_name:
            return False
        mapping = self._get_exception_severity_mapping()
        return mapping.get(self.exception_name, "warning")

    def _get_exception_severity_mapping_param(self):
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("rest.log.severity.exception.mapping")
        )
        return param.strip() if param else ""

    @tools.ormcache("self._get_exception_severity_mapping_param()")
    def _get_exception_severity_mapping(self):
        mapping = self.EXCEPTION_SEVERITY_MAPPING.copy()
        param = self._get_exception_severity_mapping_param()
        if not param:
            return mapping
        # param should be in the form
        # `[module.dotted.path.]ExceptionName:severity,ExceptionName:severity`
        for rule in param.split(","):
            if not rule.strip():
                continue
            exc_name = severity = None
            try:
                exc_name, severity = [x.strip() for x in rule.split(":")]
                if not exc_name or not severity:
                    raise ValueError
            except ValueError:
                _logger.info(
                    "Could not convert System Parameter"
                    " 'rest.log.severity.exception.mapping' to mapping."
                    " The following rule will be ignored: %s",
                    rule,
                )
            if exc_name and severity:
                mapping[exc_name] = severity
        return mapping

    def _logs_retention_days(self):
        retention = self.DEFAULT_RETENTION
        param = (
            self.env["ir.config_parameter"].sudo().get_param("rest.log.retention.days")
        )
        if param:
            try:
                retention = int(param)
            except ValueError:
                _logger.exception(
                    "Could not convert System Parameter"
                    " 'rest.log.retention.days' to integer,"
                    " reverting to the"
                    " default configuration."
                )
        return retention

    def logging_active(self):
        retention = self._logs_retention_days()
        return retention > 0

    def autovacuum(self):
        """Delete logs which have exceeded their retention duration

        Called from a cron.
        """
        deadline = datetime.now() - timedelta(days=self._logs_retention_days())
        deadline_str = datetime.strftime(deadline, tools.DEFAULT_SERVER_DATE_FORMAT)
        logs = self.search([("create_date", "<=", deadline_str)])
        if logs:
            logs.unlink()
        return True

    def _get_log_active_param(self):
        param = self.env["ir.config_parameter"].sudo().get_param("rest.log.active")
        return param.strip() if param else ""

    @tools.ormcache("self._get_log_active_param()")
    def _get_log_active_conf(self):
        """Compute log active configuration.

        Possible configuration contains a CSV like this:

            `collection_name` -> enable for all endpoints of the collection
            `collection_name.usage` -> enable for specific endpoints
            `collection_name.usage.endpoint` -> enable for specific endpoints
            `collection_name*:state` -> enable only for specific state (success, failed)

        By default matching keys are enabled for all states.

        :return: mapping by matching key / enabled states
        """
        param = self._get_log_active_param()
        conf = {}
        lines = [x.strip() for x in param.split(",") if x.strip()]
        for line in lines:
            bits = [x.strip() for x in line.split(":") if x.strip()]
            if len(bits) > 1:
                match_key = bits[0]
                # fmt: off
                states = (bits[1], )
                # fmt: on
            else:
                match_key = line
                states = ("success", "failed")
            conf[match_key] = states
        return conf

    @api.model
    def _get_matching_active_conf(self, collection, usage, method_name):
        """Retrieve conf matching current service and method.
        """
        conf = self._get_log_active_conf()
        candidates = (
            collection + "." + usage + "." + method_name,
            collection + "." + usage,
            collection,
        )
        for candidate in candidates:
            if conf.get(candidate):
                return conf.get(candidate)
