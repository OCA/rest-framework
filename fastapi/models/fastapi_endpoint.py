# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import logging
from functools import partial
from typing import Any, Awaitable, Callable, Dict, List, Type, Union

from a2wsgi import ASGIMiddleware

import odoo
from odoo import _, api, exceptions, fields, models, tools

from odoo.addons.endpoint_route_handler.registry import EndpointRegistry

from fastapi import APIRouter, FastAPI, HTTPException, Request, Response

from .. import depends, error_handlers

_logger = logging.getLogger(__name__)


class FastapiEndpoint(models.Model):

    _name = "fastapi.endpoint"
    _description = "FastAPI Endpoint"

    name: str = fields.Char(required=True, help="The title of the API.")
    description: str = fields.Text(
        help="A short description of the API. It can use Markdown"
    )
    root_path: str = fields.Char(
        required=True,
        index=True,
        compute="_compute_root_path",
        inverse="_inverse_root_path",
        readonly=False,
        store=True,
        copy=False,
    )
    app: str = fields.Selection(selection=[], required=True)
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="User",
        help="The user to use to execute the API calls.",
        default=lambda self: self.env.ref("base.public_user"),
    )
    docs_url: str = fields.Char(compute="_compute_urls")
    redoc_url: str = fields.Char(compute="_compute_urls")
    openapi_url: str = fields.Char(compute="_compute_urls")

    active: bool = fields.Boolean(default=True)

    @api.depends("root_path")
    def _compute_root_path(self):
        for rec in self:
            rec.root_path = rec._clean_root_path()

    def _inverse_root_path(self):
        for rec in self:
            rec.root_path = rec._clean_root_path()

    def _clean_root_path(self):
        root_path = (self.root_path or "").strip()
        if not root_path.startswith("/"):
            root_path = "/" + root_path
        return root_path

    _blacklist_root_paths = {"/", "/web", "/website"}

    @api.constrains("root_path")
    def _check_root_path(self):
        for rec in self:
            if rec.root_path in self._blacklist_root_paths:
                raise exceptions.UserError(
                    _(
                        "`%(name)s` uses a blacklisted root_path = `%(root_path)s`",
                        name=rec.name,
                        root_path=rec.root_path,
                    )
                )

    @api.depends("root_path")
    def _compute_urls(self):
        for rec in self:
            rec.docs_url = f"{rec.root_path}/docs"
            rec.redoc_url = f"{rec.root_path}/redoc"
            rec.openapi_url = f"{rec.root_path}/openapi.json"

    @api.model_create_multi
    def create(self, vals_list):
        rec = super().create(vals_list)
        if rec.active:
            rec._register_endpoints()
        return rec

    def write(self, vals):
        res = super().write(vals)
        self._handle_route_updates(vals)
        return res

    def _handle_route_updates(self, vals):
        if "active" in vals:
            if vals["active"]:
                self._register_endpoints()
            else:
                self._unregister_endpoints()
            return True
        refresh_endpoints = any([x in vals for x in self._routing_fields()])
        refresh_fastapi_app = (
            any([x in vals for x in self._fastapi_app_fields()]) or refresh_endpoints
        )
        if refresh_endpoints:
            self._register_endpoints()
        if refresh_fastapi_app:
            self._reset_app()
        if "user_id" in vals:
            self.get_uid.clear_cache(self)
        return False

    def unlink(self):
        self._unregister_endpoints()
        return super().unlink()

    @api.model
    def _routing_fields(self) -> List[str]:
        """The list of fields requiring to refresh the mount point of the pp
        into odoo if modified"""
        return ["root_path"]

    @api.model
    def _fastapi_app_fields(self) -> List[str]:
        """The list of fields requiring to refresh the fastapi app if modified"""
        return []

    @property
    def _endpoint_registry(self) -> EndpointRegistry:
        return EndpointRegistry.registry_for(self.env.cr.dbname)

    def _register_hook(self):
        self.search([("active", "=", True)])._register_endpoints(init=True)

    def _register_endpoints(self, init: bool = False):
        for rec in self:
            for rule in rec._make_routing_rule():
                rec._endpoint_registry.add_or_update_rule(rule, init=init)

    def _make_routing_rule(self):
        """Generator of rule for every route into the routing info"""
        self.ensure_one()
        routing = self._get_routing_info()
        for route in routing["routes"]:
            key = self._endpoint_registry_route_unique_key(route)
            endpoint_hash = hash(route)

            def endpoint(self):
                """Dummy method only used to register a route with type='fastapi'"""

            endpoint.routing = routing
            rule = self._endpoint_registry.make_rule(
                key, route, endpoint, routing, endpoint_hash
            )
            yield rule

    def _get_routing_info(self):
        self.ensure_one()
        return {
            "type": "fastapi",
            "auth": "public",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "routes": [
                f"{self.root_path}/",
                f"{self.root_path}/<path:application_path>",
            ],
            # csrf ?????
        }

    def _endpoint_registry_route_unique_key(self, route: str):
        path = route.replace(self.root_path, "")
        return f"{self._name}:{self.id}:{path}"

    def _unregister_endpoints(self):
        for rec in self:
            for route in rec._get_routing_info()["routes"]:
                key = rec._endpoint_registry_route_unique_key(route)
                rec._endpoint_registry.drop_rule(key)

    def _reset_app(self):
        self.get_app.clear_cache(self)

    @api.model
    @tools.ormcache("root_path")
    # TODO cache on thread local by db to enable to get 1 middelware by
    # thread when odoo runs in multi threads mode and to allows invalidate
    # specific entries in place og the overall cache as we have to do into
    # the _rest_app method
    def get_app(self, root_path):
        record = self.search([("root_path", "=", root_path)])
        if not record:
            return None
        return ASGIMiddleware(record._get_app())

    @api.model
    @tools.ormcache("root_path")
    def get_uid(self, root_path):
        record = self.search([("root_path", "=", root_path)])
        if not record:
            return None
        return record.user_id.id

    def _get_app(self) -> FastAPI:
        app = FastAPI(**self._prepare_fastapi_endpoint_params())
        for router in self._get_fastapi_routers():
            app.include_router(prefix=self.root_path, router=router)
        app.dependency_overrides[depends.fastapi_endpoint_id] = partial(
            lambda a: a, self.id
        )
        for exception, handler in self._get_app_exception_handlers().items():
            app.add_exception_handler(exception, handler)
        return app

    def _get_app_exception_handlers(
        self,
    ) -> Dict[
        int | Type[Exception],
        Callable[[Request, Exception], Union[Response, Awaitable[Response]]],
    ]:
        """Return a dict of exception handlers to register on the app

        The key is the exception class or status code to handle.
        The value is the handler function.

        If you need to register your own handler, you can do it by overriding
        this method and calling super(). Changes done in this way will be applied
        to all the endpoints. If you need to register a handler only for a specific
        endpoint, you can do it by overriding the _get_app_exception_handlers method
        and conditionally returning your specific handlers only for the endpoint
        you want according to the self.app value.

        Be careful to not forget to roll back the transaction when you implement
        your own error handler. If you don't, the transaction will be committed
        and the changes will be applied to the database.
        """
        self.ensure_one()
        return {
            Exception: error_handlers._odoo_exception_handler,
            HTTPException: error_handlers._odoo_http_exception_handler,
            odoo.exceptions.UserError: error_handlers._odoo_user_error_handler,
            odoo.exceptions.AccessError: error_handlers._odoo_access_error_handler,
            odoo.exceptions.MissingError: error_handlers._odoo_missing_error_handler,
            odoo.exceptions.ValidationError: error_handlers._odoo_validation_error_handler,
        }

    def _prepare_fastapi_endpoint_params(self) -> Dict[str, Any]:
        """Return the params to pass to the Fast API app constructor"""
        return {
            "title": self.name,
            "description": self.description,
            "openapi_url": self.openapi_url,
            "docs_url": self.docs_url,
            "redoc_url": self.redoc_url,
        }

    def _get_fastapi_routers(self) -> List[APIRouter]:
        """Return the api routers to use for the instance.

        This methoud must be implemented when registering a new api type.
        """
        return []
