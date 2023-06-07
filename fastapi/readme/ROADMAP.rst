The `roadmap <https://github.com/OCA/rest-framework/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement+label%3Afastapi>`_
and `known issues <https://github.com/OCA/rest-framework/issues?q=is%3Aopen+is%3Aissue+label%3Abug+label%3Afastapi>`_ can
be found on GitHub.

The **FastAPI** module provides an easy way to use WebSockets. Unfortunately, this
support is not 'yet' available in the **Odoo** framework. The challenge is high
because the integration of the fastapi is based on the use of a specific middleware
that convert the WSGI request consumed by odoo to a ASGI request. The question
is to know if it is also possible to develop the same kind of bridge for the
WebSockets and to stream large responses.
