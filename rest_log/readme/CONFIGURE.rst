Logs retention
~~~~~~~~~~~~~~

Logs are kept in database for every REST requests made by a client application.
They can be used for debugging and monitoring of the activity.

The Logs menu is shown only with Developer tools (``?debug=1``) activated.

By default, REST logs are kept 30 days.
You can change the duration of the retention by changing the System Parameter
``rest.log.retention.days``.

If the value is set to 0, the logs are not stored at all.

Logged data is: request URL and method, parameters, headers, result or error.
