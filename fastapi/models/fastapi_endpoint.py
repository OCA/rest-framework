# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import logging
from collections.abc import Callable
from functools import partial
from itertools import chain
from typing import Any

from starlette.middleware import Middleware
from starlette.routing import Mount

from odoo import _, api, exceptions, fields, models, tools

from fastapi import APIRouter, Depends, FastAPI

from ..middleware import ASGIMiddleware

_logger = logging.getLogger(__name__)


class FastapiEndpoint(models.Model):
    _name = "fastapi.endpoint"
    _inherit = "endpoint.route.sync.mixin"
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
    company_id = fields.Many2one(
        "res.company",
        compute="_compute_company_id",
        store=True,
        readonly=False,
        domain="[('user_ids', 'in', user_id)]",
    )
    save_http_session = fields.Boolean(
        string="Save HTTP Session",
        help="Whether session should be saved into the session store. This is "
        "required if for example you use the Odoo's authentication mechanism. "
        "Oherwise chance are high that you don't need it and could turn off "
        "this behaviour. Additionaly turning off this option will prevent useless "
        "IO operation when storing and reading the session on the disk and prevent "
        "unexpecteed disk space consumption.",
        default=True,
    )

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

    @api.depends("user_id")
    def _compute_company_id(self):
        for endpoint in self:
            endpoint.company_id = endpoint.user_id.company_id

    #
    # endpoint.route.sync.mixin methods implementation
    #
    def _prepare_endpoint_rules(self, options=None):
        return [rec._make_routing_rule(options=options) for rec in self]

    def _registered_endpoint_rule_keys(self):
        res = []
        for rec in self:
            routing = rec._get_routing_info()
            res.append(rec._endpoint_registry_route_unique_key(routing))
        return tuple(res)

    @api.model
    def _routing_impacting_fields(self) -> tuple[str, ...]:
        """The list of fields requiring to refresh the mount point of the pp
        into odoo if modified"""
        return ("root_path", "save_http_session")

    #
    # end of endpoint.route.sync.mixin methods implementation
    #

    def write(self, vals):
        res = super().write(vals)
        self._handle_route_updates(vals)
        return res

    def action_sync_registry(self):
        self.filtered(lambda e: not e.registry_sync).write({"registry_sync": True})

    def _handle_route_updates(self, vals):
        observed_fields = [self._routing_impacting_fields(), self._fastapi_app_fields()]
        refresh_fastapi_app = any([x in vals for x in chain(*observed_fields)])
        if refresh_fastapi_app:
            self._reset_app()
        if "user_id" in vals:
            self.env.registry.clear_cache()
        return False

    @api.model
    def _fastapi_app_fields(self) -> list[str]:
        """The list of fields requiring to refresh the fastapi app if modified"""
        return []

    def _make_routing_rule(self, options=None):
        """Generator of rule"""
        self.ensure_one()
        routing = self._get_routing_info()
        options = options or self._default_endpoint_options()
        route = "|".join(routing["routes"])
        key = self._endpoint_registry_route_unique_key(routing)
        endpoint_hash = hash(route)
        return self._endpoint_registry.make_rule(
            key, route, options, routing, endpoint_hash
        )

    def _default_endpoint_options(self):
        options = {"handler": self._default_endpoint_options_handler()}
        return options

    def _default_endpoint_options_handler(self):
        # The handler is useless in the context of a fastapi endpoint since the
        # routing type is "fastapi" and the routing is handled by a dedicated
        # dispatcher that will forward the request to the fastapi app.
        base_path = "odoo.addons.endpoint_route_handler.controllers.main"
        return {
            "klass_dotted_path": f"{base_path}.EndpointNotFoundController",
            "method_name": "auto_not_found",
        }

    def _get_routing_info(self):
        self.ensure_one()
        return {
            "type": "fastapi",
            "auth": "public",
            "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
            "routes": [
                f"{self.root_path}/",
                f"{self.root_path}/<path:application_path>",
            ],
            "save_session": self.save_http_session,
            "readonly": False,
            # csrf ?????
        }

    def _endpoint_registry_route_unique_key(self, routing: dict[str, Any]):
        route = "|".join(routing["routes"])
        path = route.replace(self.root_path, "")
        return f"{self._name}:{self.id}:{path}"

    def _reset_app(self):
        """When the app is reset we clear the cache, the system will signal to
        others instances that the cache is not up to date and that they should
        invalidate their cache as well. This is required to ensure that any change
        requiring a reset of the app is propagated to all the running instances.
        """
        self.env.registry.clear_cache()

    @api.model
    def _normalize_url_path(self, path) -> str:
        """
        Normalize a URL path:
        * Remove redundant slashes,
        * Remove trailing slash (unless it's the root),
        * Lowercase for case-insensitive matching
        """
        parts = [part.lower() for part in path.strip().split("/") if part]
        return "/" + "/".join(parts)

    @api.model
    def _is_suburl(self, path, prefix) -> bool:
        """
        Check if 'path' is a subpath of 'prefix' in URL logic:
        * Must start with the prefix followed by a slash
          This will ensure that the matching is done one the path
          parts and ensures that e.g. /a/b is not prefix of /a/bc.
        """
        path = self._normalize_url_path(path)
        prefix = self._normalize_url_path(prefix)

        if path == prefix:
            return True
        if path.startswith(prefix + "/"):
            return True
        return False

    @api.model
    def _find_first_matching_url_path(self, paths, prefix) -> str | None:
        """
        Return the first path that is a subpath of 'prefix',
        ordered by longest URL path first (most number of segments).
        """
        # Sort by number of segments (shallowest first)
        sorted_paths = sorted(
            paths,
            key=lambda p: len(self._normalize_url_path(p).split("/")),
            reverse=True,
        )

        for path in sorted_paths:
            if self._is_suburl(prefix, path):
                return path
        return None

    @api.model
    @tools.ormcache()
    def _get_id_by_root_path_map(self):
        return {r.root_path: r.id for r in self.search([])}

    @api.model
    @tools.ormcache("path")
    def _get_id_for_path(self, path):
        id_by_path = self._get_id_by_root_path_map()
        root_path = self._find_first_matching_url_path(id_by_path.keys(), path)
        return id_by_path.get(root_path)

    @api.model
    def _get_endpoint(self, path):
        id_ = self._get_id_for_path(path)
        return self.browse(id_) if id_ else None

    @api.model
    def get_app(self, path):
        record = self._get_endpoint(path)
        if not record:
            return None
        app = FastAPI()
        app.mount(record.root_path, record._get_app())
        self._clear_fastapi_exception_handlers(app)
        return ASGIMiddleware(app)

    def _clear_fastapi_exception_handlers(self, app: FastAPI) -> None:
        """
        Clear the exception handlers of the given fastapi app.

        This method is used to ensure that the exception handlers are handled
        by odoo and not by fastapi. We therefore need to remove all the handlers
        added by default when instantiating a FastAPI app. Since apps can be
        mounted recursively, we need to apply this method to all the apps in the
        mounted tree.
        """
        app.exception_handlers = {}
        for route in app.routes:
            if isinstance(route, Mount):
                self._clear_fastapi_exception_handlers(route.app)

    @api.model
    @tools.ormcache("path")
    def get_uid(self, path):
        record = self._get_endpoint(path)
        if not record:
            return None
        return record.user_id.id

    def _get_app(self) -> FastAPI:
        app = FastAPI(**self._prepare_fastapi_app_params())
        for router in self._get_fastapi_routers():
            app.include_router(router=router)
        app.dependency_overrides.update(self._get_app_dependencies_overrides())
        return app

    def _get_app_dependencies_overrides(self) -> dict[Callable, Callable]:
        # Import here to avoid circular import while waiting for lazy imports
        from ..dependencies import company_id, fastapi_endpoint_id

        return {
            fastapi_endpoint_id: partial(lambda a: a, self.id),
            company_id: partial(lambda a: a, self.company_id.id),
        }

    def _prepare_fastapi_app_params(self) -> dict[str, Any]:
        """Return the params to pass to the Fast API app constructor"""
        return {
            "title": self.name,
            "description": self.description,
            "middleware": self._get_fastapi_app_middlewares(),
            "dependencies": self._get_fastapi_app_dependencies(),
        }

    def _get_fastapi_routers(self) -> list[APIRouter]:
        """Return the api routers to use for the instance.

        This method must be implemented when registering a new api type.
        """
        return []

    def _get_fastapi_app_middlewares(self) -> list[Middleware]:
        """Return the middlewares to use for the fastapi app."""
        return []

    def _get_fastapi_app_dependencies(self) -> list[Depends]:
        """Return the dependencies to use for the fastapi app."""
        # Import here to avoid circular import too
        from ..dependencies import accept_language

        return [Depends(accept_language)]
