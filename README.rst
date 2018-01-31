.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=========
Base Rest
=========

Base addon to implement REST service in an efficient and secured way

Installation
============

A generic REST Full controller should look like

::

    from  odoo.addons.base_rest.controllers import main

    def MyRestController(main.RestController):

        ROOT_PATH = '/my_rest_api'
        @route([
            ROOT_PATH + '<string:_service_name>',
            ROOT_PATH + '<string:_service_name>/search',
            ROOT_PATH + '<string:_service_name>/<int:_id>',
            ROOT_PATH + '<string:_service_name>/<int:_id>/get'
        ], methods=['GET'], auth="user", csrf=False)
        def get(self, _service_name, _id=None, **params):
            method_name = 'get' if _id else 'search'
            return self._process_method(_service_name, method_name, _id, params)

        @route([
            ROOT_PATH + '<string:_service_name>',
            ROOT_PATH + '<string:_service_name>/<string:method_name>',
            ROOT_PATH + '<string:_service_name>/<int:_id>',
            ROOT_PATH + '<string:_service_name>/<int:_id>/<string:method_name>'
        ], methods=['POST'], auth="user", csrf=False)
        def modify(self, _service_name, _id=None, method_name=None, **params):
            if not method_name:
                method_name = 'update' if _id else 'create'
            if method_name == 'get':
                _logger.error("HTTP POST with method name 'get' is not allowed. "
                              "(service name: %s)", _service_name)
                raise BadRequest()
            return self._process_method(_service_name, method_name, _id, params)

        @route([
            ROOT_PATH + '<string:_service_name>/<int:_id>',
        ], methods=['PUT'], auth="user", csrf=False)
        def update(self, _service_name, _id, **params):
            return self._process_method(_service_name, 'update', _id, params)

        @route([
            ROOT_PATH + '<string:_service_name>/<int:_id>',
        ], methods=['DELETE'], auth="user", csrf=False)
        def delete(self, _service_name, _id):
            return self._process_method(_service_name, 'delete', _id)


#. Do this ...

Configuration
=============

To configure this module, you need to:

#. Go to ...

.. figure:: path/to/local/image.png
   :alt: alternative description
   :width: 600 px

Usage
=====

To use this module, you need to:

#. Go to ...

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/{repo_id}/{branch}

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* ...

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Laurent Mignon <laurent.mignon@acsone.eu>
* Sébastien Beau <sebastien.beau@akretion.com>

Funders
-------

The development of this module has been financially supported by:

* Company 1 name
* Company 2 name

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
