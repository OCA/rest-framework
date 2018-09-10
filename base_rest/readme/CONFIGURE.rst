If an error occurs when calling a method of a service (ie missing parameter,
..) the system returns only a general description of the problem without
details. This is done on purpose to ensure maximum opacity on implementation
details and therefore lower security issue.

This restriction can be problematic when the services are accessed by an
external system in development. To know the details of an error it is indeed
necessary to have access to the log of the server. It is not always possible
to provide this kind of access. That's why you can configure the server to run
these services in development mode.

To run the REST API in development mode you must add the option
'**base_rest_dev_mode=1**' in the server config file.

When the REST API runs in development mode, the original description and a
stack trace is returned in case of error. **Be careful to don't use this mode
in production**.