# Copyright 2019 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import inspect
import textwrap

from apispec import APISpec

from odoo.http import request

from ..core import _rest_services_databases
from ..tools import ROUTING_DECORATOR_ATTR
from .rest_method_param_plugin import RestMethodParamPlugin
from .rest_method_security_plugin import RestMethodSecurityPlugin
from .restapi_method_route_plugin import RestApiMethodRoutePlugin


class BaseRestServiceAPISpec(APISpec):
    """
    APISpec object from base.rest.service component
    """

    def __init__(self, service_component, **params):
        self._service = service_component
        super().__init__(
            title=f"{self._service._usage} REST services",
            version="",
            openapi_version="3.0.0",
            info={
                "description": textwrap.dedent(
                    getattr(self._service, "_description", "") or ""
                )
            },
            servers=self._get_servers(),
            plugins=self._get_plugins(),
        )
        self._params = params

    def _get_servers(self):
        env = self._service.env
        services_registry = _rest_services_databases.get(env.cr.dbname, {})
        collection_path = ""
        for path, spec in list(services_registry.items()):
            if spec["collection_name"] == self._service._collection:
                collection_path = path
                break
        base_domain = (
            env["ir.config_parameter"].sudo().get_param("web.base.url").strip("/")
        )
        current_domain = request.httprequest.url_root.strip("/")
        domains = [base_domain]
        if base_domain != current_domain:
            domains.append(current_domain)
        res = []
        for domain in domains:
            res.append(
                {
                    "url": "/".join(
                        [domain, collection_path.strip("/"), self._service._usage]
                    )
                }
            )

        return res

    def _get_plugins(self):
        return [
            RestApiMethodRoutePlugin(self._service),
            RestMethodParamPlugin(self._service),
            RestMethodSecurityPlugin(self._service),
        ]

    def _add_method_path(self, method):
        description = textwrap.dedent(method.__doc__ or "")
        routing = getattr(method, ROUTING_DECORATOR_ATTR)
        for paths, method in routing["routes"]:
            for path in paths:
                self.path(
                    path,
                    operations={method.lower(): {"summary": description}},
                    **{ROUTING_DECORATOR_ATTR: routing},
                )

    def generate_paths(self):
        for _name, method in inspect.getmembers(self._service, inspect.ismethod):
            routing = getattr(method, ROUTING_DECORATOR_ATTR, None)
            if not routing:
                continue
            self._add_method_path(method)
