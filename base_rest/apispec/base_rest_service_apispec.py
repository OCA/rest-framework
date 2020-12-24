# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import inspect
import textwrap

from apispec import APISpec

from ..core import _rest_services_databases
from .rest_method_param_plugin import RestMethodParamPlugin
from .restapi_method_route_plugin import RestApiMethodRoutePlugin


class BaseRestServiceAPISpec(APISpec):
    """
    APISpec object from base.rest.service component
    """

    def __init__(self, service_component):
        self._service = service_component
        super(BaseRestServiceAPISpec, self).__init__(
            title="%s REST services" % self._service._usage,
            version="",
            openapi_version="3.0.0",
            info={
                "description": textwrap.dedent(
                    getattr(self._service, "_description", "")
                )
            },
            servers=self._get_servers(),
            plugins=[
                RestApiMethodRoutePlugin(self._service),
                RestMethodParamPlugin(self._service),
            ],
        )
        self._generate_paths()

    def _get_servers(self):
        env = self._service.env
        services_registry = _rest_services_databases.get(env.cr.dbname, {})
        collection_path = ""
        for path, spec in list(services_registry.items()):
            if spec["collection_name"] == self._service._collection:
                collection_path = path
                break
        base_url = env["ir.config_parameter"].sudo().get_param("web.base.url")
        return [
            {
                "url": "%s/%s/%s"
                % (
                    base_url.strip("/"),
                    collection_path.strip("/"),
                    self._service._usage,
                )
            }
        ]

    def _add_method_path(self, method):
        description = textwrap.dedent(method.__doc__ or "")
        routing = method.routing
        for paths, method in routing["routes"]:
            for path in paths:
                self.path(
                    path,
                    operations={method.lower(): {"summary": description}},
                    routing=routing,
                )

    def _generate_paths(self):
        for _name, method in inspect.getmembers(self._service, inspect.ismethod):
            routing = getattr(method, "routing", None)
            if not routing:
                continue
            self._add_method_path(method)
