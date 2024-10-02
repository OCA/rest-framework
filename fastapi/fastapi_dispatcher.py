# Copyright 2022 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from contextlib import contextmanager
from io import BytesIO

from werkzeug.exceptions import InternalServerError

from odoo.http import Dispatcher, request

from .context import odoo_env_ctx


class FastApiDispatcher(Dispatcher):
    routing_type = "fastapi"

    @classmethod
    def is_compatible_with(cls, request):
        return True

    def dispatch(self, endpoint, args):
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
        with self._manage_odoo_env(uid):
            for r in app(environ, self._make_response):
                data.write(r)
            return self.request.make_response(
                data.getvalue(), headers=self.headers, status=self.status
            )

    def handle_error(self, exc):
        # At this stage all the normal exceptions are handled by FastAPI
        # and we should only have InternalServerError occurring after the
        # FastAPI app has been called.
        return InternalServerError()  # pragma: no cover

    def _make_response(self, status_mapping, headers_tuple, content):
        self.status = status_mapping[:3]
        self.headers = dict(headers_tuple)

    def _get_environ(self):
        try:
            # normal case after
            # https://github.com/odoo/odoo/commit/cb1d057dcab28cb0b0487244ba99231ee292502e
            httprequest = self.request.httprequest._HTTPRequest__wrapped
        except AttributeError:
            # fallback for older odoo versions
            # The try except is the most efficient way to handle this
            # as we expect that most of the time the attribute will be there
            # and this code will no more be executed if it runs on an up to
            # date odoo version. (EAFP: Easier to Ask for Forgiveness than Permission)
            httprequest = self.request.httprequest
        environ = httprequest.environ
        environ["wsgi.input"] = httprequest._get_stream_for_parsing()
        return environ

    @contextmanager
    def _manage_odoo_env(self, uid=None):
        env = request.env
        accept_language = request.httprequest.headers.get("Accept-language")
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
