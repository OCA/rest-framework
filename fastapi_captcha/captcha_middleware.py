# Copyright 2025 Akretion (http://www.akretion.com).
# @author Florian Mounier <florian.mounier@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from starlette.middleware.base import BaseHTTPMiddleware

from odoo.exceptions import AccessError

from odoo.addons.fastapi.context import odoo_env_ctx


class CaptchaMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, endpoint_id, root_path, routes_regex=None):
        super().__init__(app)
        self.endpoint_id = endpoint_id
        self.root_path = root_path
        self.routes_regex = routes_regex

    async def dispatch(self, request, call_next):
        url = request.url.path.replace(self.root_path, "", 1)
        if self.routes_regex and not any(
            rex.fullmatch(url) for rex in self.routes_regex
        ):
            return await call_next(request)

        env = odoo_env_ctx.get()
        endpoint = env["fastapi.endpoint"].sudo().browse(self.endpoint_id)
        token = request.headers.get("X-Captcha-Token")
        if not token:
            raise AccessError(
                env._("Captcha token not found in headers"),
            )
        try:
            endpoint.validate_captcha(token)
        except AccessError as e:
            raise e
        except OSError as e:
            raise AccessError(
                env._("Captcha validation failed: %s") % str(e),
            ) from e
        response = await call_next(request)
        return response
