========================
REST Controllers in Odoo
========================

Introduction
============

This module allows you to define REST controllers in Odoo.
Normally this is not possible, because Odoo assumes that all json requests
are JSON-RPC and does some "magic" stuff that doesn't let you return
the kind of responses used by REST APIs.

Usage
=====

You can define a REST controller simply by adding ``subtype='rest'``
in the ``route`` decorator, for example::

    from odoo.http import route, request

    @http.route('/api/partners', subtype='rest', auth='public')
    def partners_list(self, **params):
        return request.env['res.partner'].search_read(
            [], ['name', 'street'], limit=2)

If you now go to ``/api/partners``, you'll get a JSON response
(``Content-Type`` and ``Content-Length`` headers set) with
the following body (for example)::

    [
        {"street": "Main street, 2", "id": 123, "name": "A big company"},
        {"street": false, "id": 124, "name": "A BIGGER company"}
    ]

The dict returned by ``search_read`` has been automatically converted to its
JSON representation. This is an example of one of the automatic conversions of
the return data of REST controllers, here is the complete list:

* If you return an instance of ``http.Response``, it will be returned as-is
* If you return a tuple, it will be considered as ``(status_code, json_data)``
* If you return an integer, that will be considered as the status code, and
  the response will have no body
* Anything else will be treated as the body data and will be serialized as
  JSON and sent in a 200 Response

``json_data`` can be any JSON-serializable python object (usually dict or list)
and it will be automatically converted to its JSON representation
using ``json.dumps()``

Credits
=======

Contributors
------------

* Leonardo Donelli (LeartS) <donelli@monksoftware.it>

Funders
-------

The development of this module has been financially supported by:

* MONK Software