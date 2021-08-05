Authentication
~~~~~~~~~~~~~~

To authenticate you need to :code:`POST` a request on :code:`[ODOO HOST]/session/auth/login` with the
following body::

    {
        "db": [DB_NAME],
        "login": [LOGIN],
        "password": [PASSWORD]
    }

:code:`"db"` is not mandatory if Odoo is able to determine it unequivocally (e.g. single database server or
:code:`dbfilter` parameter). If the authentication is successful, the response will contain (in addition to the usual
response of the JSON-RPC authentication)::

    {
        ...
        "session": {
            "sid": "ff6b4bac7a590e7960abfc0ac38361433ecac1d6",
            "expires_at": "2021-09-21 16:53:56"
        }
    }

This :code:`sid` value can then be sent in subsequent requests in the following ways:

* header :code:`X-Openerp-Session-Id`
* cookie named `session_id`
* request param `session_id`

Logout
~~~~~~

To logout you need to :code:`POST` a request on :code:`[ODOO HOST]/session/auth/logout` with an empty body.
