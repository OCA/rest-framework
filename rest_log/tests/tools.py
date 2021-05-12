# -*- encoding: utf-8 -*-
# Part of Odoo. See Odoo 13 LICENSE file for full copyright and licensing details.


import werkzeug

import odoo


class DotDict(dict):
    """Helper for dot.notation access to dictionary attributes

        E.g.
          foo = DotDict({'bar': False})
          return foo.bar
    """

    def __getattr__(self, attrib):
        val = self.get(attrib)
        return DotDict(val) if type(val) is dict else val


class MockObject(object):
    _log_call = []

    def __init__(self, *args, **kwargs):
        self.__dict__ = kwargs

    def __call__(self, *args, **kwargs):
        self._log_call.append((args, kwargs))
        return self

    def __getitem__(self, index):
        return self


def werkzeugRaiseNotFound(*args, **kwargs):
    raise werkzeug.exceptions.NotFound()


class MockRequest(object):
    """ Class with context manager mocking odoo.http.request for tests """

    def __init__(self, env, **kw):
        app = MockObject(
            routing={
                "type": "http",
                "website": True,
                "multilang": kw.get("multilang", True),
            }
        )
        app.get_db_router = app.bind = app.match = app
        if not kw.get("routing", True):
            app.match = werkzeugRaiseNotFound

        lang = kw.get("lang")
        if not lang:
            lang_code = kw.get("context", {}).get(
                "lang", env.context.get("lang", "en_US")
            )
            lang = env["res.lang"]._lang_get(lang_code)

        context = kw.get("context", {})
        context.setdefault("lang", lang_code)

        self.request = DotDict(
            {
                "context": context,
                "db": None,
                "env": env,
                "httprequest": {
                    "path": "/hello/",
                    "app": app,
                    "environ": {"REMOTE_ADDR": "127.0.0.1"},
                    "cookies": kw.get("cookies", {}),
                },
                "lang": lang,
                "redirect": werkzeug.utils.redirect,
                "session": {
                    "geoip": {"country_code": kw.get("country_code")},
                    "debug": False,
                    "sale_order_id": kw.get("sale_order_id"),
                },
                "website": kw.get("website"),
            }
        )

    def __enter__(self):
        odoo.http._request_stack.push(self.request)
        return self.request

    def __exit__(self, exc_type, exc_value, traceback):
        odoo.http._request_stack.pop()
