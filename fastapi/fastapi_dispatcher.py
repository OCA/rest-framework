from contextlib import contextmanager
from io import BytesIO

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
        app = request.env["fastapi.app"].sudo().get_app(root_path)
        data = BytesIO()
        with self._manage_odoo_env():
            for r in app(environ, self._make_response):
                data.write(r)
            return self.request.make_response(
                data.getvalue(), headers=self.headers, status=self.status
            )

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
    def _manage_odoo_env(self):
        token = odoo_env_ctx.set(request.env)
        try:
            yield
        finally:
            odoo_env_ctx.reset(token)
