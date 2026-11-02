This module allows to store request and response logs for any API.

When a response is logged, the header `API_LOG_ENTRY_ID` is injected in the response header.
This header stores the identifier of the log record produced from the response.

A scheduled action "API Log: Delete old logs" is available to automatically
delete old API log records. It is **disabled by default**.

To enable it, go to Settings > Technical > Automation > Scheduled Actions
and activate "API Log: Delete old logs".

The retention period (in days) is configurable through the system parameter
`api_log.retention_days`, which defaults to 180 days. Logs with a
`request_date` older than this threshold are deleted when the cron runs.
