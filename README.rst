========================
REST Controllers in Odoo
========================

Introduction
============

This module allows you to define REST controllers in Odoo.
Normally this is not possible, because Odoo assumes that all json requests
are JSON-RPC and does some "magic" stuff that doesn't let you return
the kind of responses usually returned by REST APIs.
With this module, not only you can workaround the JSON-RPC limitation,
but you get a lot of convenience methods to quickly and easily implement
REST APIs -- for example, by having recordset be converted automagically
to a JSON representation!

Usage
=====

Basic usage
-----------

You define REST controllers like normal odoo controllers,
you'll only need to use the
``odoo.addons.base_request_rest.http.restroute`` decorator
(or ``restroutemulti`` or ``restroutesingle``, see below) instead
of the standard ``odoo.http.route`` one.

For example::

    from odoo.addons.base_request_rest.http import restroute

    @restroute('/api/partners')
    def list_partners(self, **params):
        return request.env['res.partner'].search_read(
            [], ['name', 'street'], limit=2)

If you now go to ``/api/partners``, you'll get a JSON response
(i.e. with the appropriate HTTP headers set) with
the following body (for example)::

    {
        "status": "success",
        "data": [
            {"street": "Main street, 2", "id": 123, "name": "A big company"},
            {"street": false, "id": 124, "name": "A BIGGER company"}
        ]
    }

The dict returned by ``search_read`` has been automatically converted to its
JSON representation, and the JSON response data has been automatically wrapped
in a response object according to the `jsend specification`_

.. _jsend specification: https://labs.omniti.com/labs/jsend

Automatic return value conversion
---------------------------------

The dict is only one of the supported return types that are automatically
converted to appropriate HTTP responses. In fact, from your controllers
you can return:

* An instances of ``http.Response``, which will be returned as-is
* An integer, which will be used as the response status code (no body)
* Any base type, list, dict or tuple (let's call these *JSON-serializable objects*):
  will be serialized using ``json.dumps`` and returned with status code 200
* A tuple (int, *JSON-serializable object*): like above, with an explicit status code
* Last, but definitely not least.. return directly a recordset that inherits
  from ``rest.mixin`` ! Keep reading to see how...

rest.mixin
==========

``rest.mixin`` is an abstract model that you can make other models inherit in
order to gain some super convenient rest functionalities:

* Easy to define fields to export with name mapping: you only need to declare
  a ``_rest_fields_map`` attribute in the class that maps odoo fields
  to api keys in the returned JSON
* Automatic JSON serialization: return recordset directly from your controller,
  it will be serialized to JSON automatically in the response.
* Customizable (de)serialization: rest.mixin provides the ``to_json`` and
  ``from_json`` methods that you can override to completely customize how
  records are serialized.

For example, using ``mixin``, this is all you have to do to create
a read-only API that exposes your projects and projects' tasks::


    class RESTProjectProject(models.Model):
       _name = 'project.project'
       _inherit = ['project.project', 'rest.mixin']

       _rest_fields_map = {
            'id': 'id',
            'name': 'name',
            'user_id': 'projectManager',
        }

    class RESTProjectProject(models.Model):
        _name = 'project.task'
        _inherit = ['project.task', 'rest.mixin']


    @restroutemulti('/projects')
    def list_projects(self):
        return request.env['project.project'].search([])

    @restroutesingle('/projects/<model("project.project"):project>')
    def get_project(self, project):
        return project

    @restroutemulti('/projects/<model("project.project"):project>/tasks')
    def list_project_tasks(self, project):
        return project.task_ids

Notes
=====

By deafult the controllers defined using the restroute* decorators are prefixed
with ``/rest``. So, for example, @restroutemulti('/projects') will be
published under ``/rest/projects``. You can change this default prefix by
setting the related variable before importing your controllers; for
example write the following in your module's main __init__.py::


    from odoo.addons.base_request_rest import http
    http.API_PREFIX = '/api/v1'


Credits
=======

Contributors
------------

* Leonardo Donelli (LeartS) <donelli@monksoftware.it>

Funders
-------

The development of this module has been financially supported by:

* MONK Software