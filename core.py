# -*- coding: utf-8 -*-
# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


class RestServicesDatabases(dict):
    """ Holds a registry of REST services for each database """


_rest_services_databases = RestServicesDatabases()


class RestServicesRegistry(dict):
    """ Holds a registry of REST services where key is the root of the path on
    which the methods of your ` RestController`` are registred and value is the
    name of the collection on which your ``RestServiceComponent`` implementing
    the business logic of your service is registered."""
