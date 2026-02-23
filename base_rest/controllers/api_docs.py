# Copyright 2018 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
from contextlib import contextmanager

from odoo.http import Controller, request, route

from odoo.addons.component.core import WorkContext

from ..core import _rest_services_databases
from .main import _PseudoCollection


class ApiDocsController(Controller):
    def make_json_response(self, data, headers=None, cookies=None):
        data = json.dumps(data)
        if headers is None:
            headers = {}
        headers["Content-Type"] = "application/json"
        return request.make_response(data, headers=headers, cookies=cookies)

    @route(
        ["/api-docs", "/api-docs/index.html"],
        methods=["GET"],
        type="http",
        auth="public",
    )
    def index(self, **params):
        self._get_api_urls()
        primary_name = params.get("urls.primaryName")
        swagger_settings = {
            "urls": self._get_api_urls(),
            "urls.primaryName": primary_name,
        }
        values = {"swagger_settings": swagger_settings}
        return request.render("base_rest.openapi", values)

    @route("/api-docs/<path:collection>/<string:service_name>.json", auth="public")
    def api(self, collection, service_name):
        with self.service_and_controller_class(collection, service_name) as (
            service,
            controller_class,
        ):
            openapi_doc = service.to_openapi(
                default_auth=controller_class._default_auth
            )
            return self.make_json_response(openapi_doc)

    def _get_api_urls(self):
        """
        This method lookup into the dictionary of registered REST service
        for the current database to built the list of available REST API
        :return:
        """
        services_registry = _rest_services_databases.get(request.env.cr.dbname, {})
        api_urls = []
        for rest_root_path, spec in list(services_registry.items()):
            collection_path = rest_root_path[1:-1]  # remove '/'
            collection_name = spec["collection_name"]
            for service in self._get_service_in_collection(collection_name):
                api_urls.append(
                    {
                        "name": f"{collection_path}: {service._usage}",
                        "url": f"/api-docs/{collection_path}/{service._usage}.json",
                    }
                )
        api_urls = sorted(api_urls, key=lambda k: k["name"])
        return api_urls

    def _filter_service_components(self, components):
        reg_model = request.env["rest.service.registration"]
        return [c for c in components if reg_model._filter_service_component(c)]

    def _get_service_in_collection(self, collection_name):
        with self.work_on_component(collection_name) as work:
            components = work.components_registry.lookup(collection_name)
            services = self._filter_service_components(components)
            services = [work.component(usage=s._usage) for s in services]
        return services

    @contextmanager
    def service_and_controller_class(self, collection_path, service_name):
        """
        Return the component that implements the methods of the requested
        service.
        :param collection_path:
        :param service_name:
        :return: an instance of invader.service component,
                 the base controller class serving the service
        """
        services_spec = self._get_services_specs(collection_path)
        collection_name = services_spec["collection_name"]
        controller_class = services_spec["controller_class"]
        with self.work_on_component(collection_name) as work:
            service = work.component(usage=service_name)
            yield service, controller_class

    @contextmanager
    def work_on_component(self, collection_name):
        """
        Return the all the components implementing REST services
        :param collection_name:
        :return: a WorkContext instance
        """

        collection = _PseudoCollection(collection_name, request.env)
        yield WorkContext(model_name="rest.service.registration", collection=collection)

    def _get_services_specs(self, path):
        services_registry = _rest_services_databases.get(request.env.cr.dbname, {})
        return services_registry["/" + path + "/"]
