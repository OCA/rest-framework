# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
import logging
from contextlib import contextmanager
from io import BytesIO

from odoo.api import Environment, Environments
from odoo.http import request as odoo_request
from odoo.tools import classproperty

from .context import odoo_env_ctx, odoo_environments_ctx

_logger = logging.getLogger(__name__)


class FastApiDispatcher:
    routing_type = "fastapi"

    @classmethod
    def is_compatible_with(cls, request):
        return True

    @property
    def request(self):
        return odoo_request

    def dispatch(self, *args, **kwargs):
        # don't parse the httprequest let starlette parse the stream
        self.request.params = {}  # dict(self.request.get_http_params(), **args)
        environ = self._get_environ()
        root_path = "/" + environ["PATH_INFO"].split("/")[1]
        # TODO store the env into contextvar to be used by the odoo_env
        # depends method
        fastapi_endpoint = self.request.env["fastapi.endpoint"].sudo()
        app = fastapi_endpoint.get_app(root_path)
        uid = fastapi_endpoint.get_uid(root_path)
        data = BytesIO()
        with self._manage_odoo_env(uid), patch_odoo_environment():
            for r in app(environ, self._make_response):
                data.write(r)
            response = self.request.make_response(data.getvalue(), headers=self.headers)
            response.status = self.status
            return response

    def handle_error(self, exc):
        pass

    def _make_response(self, status_mapping, headers_tuple, content):
        self.status = status_mapping[:3]
        self.headers = dict(headers_tuple)

    def _get_environ(self):
        environ = self.request.httprequest.environ
        environ["wsgi.input"] = self.request.httprequest._get_stream_for_parsing()
        return environ

    @contextmanager
    def _manage_odoo_env(self, uid=None):
        env = self.request.env
        # add authenticated_partner_id=False in the context
        # to ensure that the ir.rule defined for user's endpoint can be
        # evaluated even if not authenticated partner is set
        env = env(context=dict(env.context, authenticated_partner_id=False))
        accept_language = self.request.httprequest.headers.get("Accept-language")
        context = env.context
        if accept_language:
            lang = (
                env["res.lang"].sudo()._get_lang_from_accept_language(accept_language)
            )
            if lang:
                env = env(context=dict(context, lang=lang))
        if uid:
            env = env(user=uid)
        token = odoo_env_ctx.set(env)
        try:
            yield
        finally:
            odoo_env_ctx.reset(token)


@classproperty
def contextvars_envs(_cls):
    return odoo_environments_ctx.get()


@classmethod  # type: ignore
@contextmanager
def contextvars_manage(_cls):
    """Context manager for a set of environments."""
    if odoo_environments_ctx.get():
        yield
    else:
        try:
            odoo_environments_ctx.set(Environments())
            _logger.debug("envs manage start")
            yield
        finally:
            _logger.debug("envs manage end")
            odoo_environments_ctx.set(())


@classmethod  # type: ignore
def contextvars_reset(_cls):
    """Clear the set of environments.
    This may be useful when recreating a registry inside a transaction.
    """
    odoo_environments_ctx.set(Environments())


@contextmanager
def patch_environment_envs() -> None:
    envs = Environment.envs
    Environment.envs = contextvars_envs
    try:
        yield
    finally:
        Environment.envs = envs


@contextmanager
def patch_environment_manage() -> None:
    manage = Environment.manage
    Environment.manage = contextvars_manage
    try:
        yield
    finally:
        Environment.manage = manage


@contextmanager
def patch_environment_reset() -> None:
    reset = Environment.reset
    Environment.reset = contextvars_reset
    try:
        yield
    finally:
        Environment.reset = reset


@contextmanager
def patch_environement_local() -> None:
    """Patch odoo Environment _local attribute to use contextvars.
    and ensure that the cache is compliant with the asyncio event loop.
    """
    _local = Environment._local
    token = odoo_environments_ctx.set(_local.environments)
    try:
        delattr(Environment, "_local")  # to be sure it is not used
        yield
    finally:
        odoo_environments_ctx.reset(token)
        Environment._local = _local


@contextmanager
def patch_odoo_environment() -> None:
    # fmt: off
    with patch_environment_envs(), patch_environment_manage(), \
            patch_environment_reset(), patch_environement_local():
        yield
    # fmt: on
