When exposing REST services is often useful to see what's happening
especially in case of errors.

This module add DB logging for REST requests.
It also inject in the response the URL of the log entry created.

NOTE: this feature was implemented initially inside shopfloor app.
If shopfloor is installed, log records will be copied from its table.
