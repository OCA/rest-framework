When exposing REST services is often useful to see what's happening
especially in case of errors.

This module add DB logging for REST requests. It also inject in the
response the URL of the log entry created.

It can also enable profiling for selected REST endpoints. When profiling is
active, the request execution is wrapped by Odoo's profiler and results are
stored in `ir_profile`.

NOTE: this feature was implemented initially inside shopfloor app. Up to
version 13.0.1.2.1 of this module, if shopfloor is installed, log
records will be copied from its table.
