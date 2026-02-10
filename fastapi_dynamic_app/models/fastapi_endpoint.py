# Copyright 2024 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from collections.abc import Callable
from itertools import groupby
from typing import Annotated, Any

from odoo import Command, api, fields, models

from odoo.addons.base.models.res_partner import Partner
from odoo.addons.fastapi.dependencies import (
    authenticated_partner_from_basic_auth_user,
    authenticated_partner_impl,
    odoo_env,
)
from odoo.addons.fastapi.models.fastapi_endpoint_demo import (
    api_key_based_authenticated_partner_impl,
)

from fastapi import APIRouter, Depends, FastAPI


class FastapiEndpoint(models.Model):
    _inherit = "fastapi.endpoint"

    app: str = fields.Selection(
        selection_add=[("dynamic", "Dynamic Endpoint")], ondelete={"dynamic": "cascade"}
    )
    router_ids = fields.Many2many(
        "fastapi.router",
        string="Routers",
        help="The routers to use on this endpoint.",
    )

    router_option_ids = fields.One2many(
        "fastapi.endpoint.router.option",
        "endpoint_id",
        compute="_compute_router_option_ids",
        store=True,
        readonly=False,
        string="Router Options",
        help="The options to use on the routers.",
    )

    dynamic_auth_method = fields.Selection(
        selection=[
            (
                "http_basic",
                "HTTP Basic",
            ),
            (
                "demo_api_key",
                "Dummy Api Key For Demo",
            ),
            (
                "demo_specific_partner",
                "Specific Partner For Demo",
            ),
        ],
        string="Auth method",
    )

    dynamic_specific_partner_id = fields.Many2one(
        "res.partner",
        string="Specific Partner",
        help="The partner to use for the specific partner demo.",
    )

    @api.depends("router_ids")
    def _compute_router_option_ids(self):
        for rec in self:
            # Use name module key to avoid virtual ids problems
            actual_routers = {
                tuple(getattr(router, key) for key in ("name", "module"))
                for router in rec.router_ids
            }
            options_to_remove = rec.router_option_ids.filtered(
                lambda router_option, actual_routers=actual_routers: (
                    (
                        router_option.router_id.name,
                        router_option.router_id.module,
                    )
                    not in actual_routers
                )
            )
            actual_router_options = {
                tuple(getattr(router, key) for key in ("name", "module"))
                for router in rec.router_option_ids.mapped("router_id")
            }
            options_to_create = rec.router_ids.filtered(
                lambda r, actual_router_options=actual_router_options: (
                    (r.name, r.module) not in actual_router_options
                )
            )
            rec.router_option_ids = [
                # Delete options for removed routers
                (
                    Command.UNLINK,
                    opt.id,
                )
                for opt in options_to_remove
            ] + [
                # Create missing options for new routers
                (
                    Command.CREATE,
                    0,
                    {
                        "router_id": router.id,
                        "endpoint_id": rec.id,
                    },
                )
                for router in options_to_create
            ]

    def _get_view(self, view_id=None, view_type="form", **options):
        # Sync once per registry instance, if a module is installed after the first call
        # a new registry will be created and the routers will be synced again
        if not hasattr(self.env.registry, "_fasapi_routers_synced"):
            self.env["fastapi.router"].sync()
            self.env.registry._fasapi_routers_synced = True
        return super()._get_view(view_id=view_id, view_type=view_type, **options)

    def _get_fastapi_routers(self) -> list[APIRouter]:
        routers = super()._get_fastapi_routers()

        if self.app == "dynamic":
            routers += [
                router_option.router_id._get_router()
                for router_option in self.router_option_ids
                if not router_option.prefix
            ]

        return routers

    def _get_app(self):
        app = super()._get_app()

        if self.app == "dynamic":
            prefixed_routers = groupby(
                self.router_option_ids,
                lambda r: r.prefix,
            )
            for prefix, router_options in prefixed_routers:
                if not prefix:
                    # Handled in _get_fastapi_routers
                    continue
                router_options = self.env["fastapi.endpoint.router.option"].browse(
                    router_option.id for router_option in router_options
                )
                if any(router_option.auth_method for router_option in router_options):
                    sub_app = FastAPI()
                    for router in router_options.mapped("router_id"):
                        sub_app.include_router(router._get_router())
                    sub_app.dependency_overrides.update(
                        self._get_app_dependencies_overrides()
                    )
                    auth_router = next(
                        router_option
                        for router_option in router_options
                        if router_option.auth_method
                    )
                    sub_app.dependency_overrides[authenticated_partner_impl] = (
                        self._get_authenticated_partner_from_method(
                            **auth_router.read()[0]
                        )
                    )

                    app.mount(prefix, sub_app)

                else:
                    for router in router_options.mapped("router_id"):
                        app.include_router(router._get_router(), prefix=prefix)

        return app

    def _get_app_dependencies_overrides(self) -> dict[Callable, Callable]:
        overrides = super()._get_app_dependencies_overrides()

        if self.app == "dynamic":
            auth = self._get_authenticated_partner_from_method(
                **{
                    key.replace("dynamic_", ""): value
                    for key, value in self.read()[0].items()
                },
            )
            if auth:
                overrides[authenticated_partner_impl] = auth

        return overrides

    @api.model
    def _get_authenticated_partner_from_method(
        self, auth_method, **options
    ) -> Callable:
        if auth_method == "http_basic":
            return authenticated_partner_from_basic_auth_user

        if auth_method == "demo_api_key":
            return api_key_based_authenticated_partner_impl

        if auth_method == "demo_specific_partner" and "specific_partner_id" in options:

            def endpoint_specific_based_authenticated_partner_impl(
                env: Annotated[api.Environment, Depends(odoo_env)],
            ) -> Partner:
                """A dummy implementation that takes the configured partner
                on the endpoint."""
                return env["res.partner"].browse(options["specific_partner_id"][0])

            return endpoint_specific_based_authenticated_partner_impl

    def _prepare_fastapi_app_params(self) -> dict[str, Any]:
        params = super()._prepare_fastapi_app_params()

        if self.app == "dynamic":
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
            params["openapi_tags"] = params.get("openapi_tags", []) + [
                {
                    "name": prefix,
                    "description": "Sub application",
                    "externalDocs": {
                        "description": "Documentation",
                        "url": f"{base_url}{self.root_path}{prefix}/docs",
                    },
                }
                for prefix in {
                    router_option.prefix
                    for router_option in self.router_option_ids
                    if router_option.prefix and router_option.auth_method
                }
            ]

        return params
