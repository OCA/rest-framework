import collections
import json

from odoo import http


class RESTRequest(http.WebRequest):
    """ Handler for the ``rest`` request type.
    The handler method's result can be:
    * a falsy value, in which case the HTTP response will be an
      `HTTP 204`_ (No Content)
    * a werkzeug Response object, which is returned as-is
    * a ``str`` or ``unicode``, will be wrapped in a Response object and
      interpreted as HTML
    .. _HTTP 204: http://tools.ietf.org/html/rfc7231#section-6.3.5
    """
    _request_type = "http"

    def __init__(self, *args):
        super(RESTRequest, self).__init__(*args)
        params = collections.OrderedDict(self.httprequest.args)
        params.update(self.httprequest.form)
        params.update(self.httprequest.files)
        params.pop('session_id', None)
        self.params = params

    def json_response(self, status=200, data=None):
        headers = None
        content_type = None
        body = None
        if data is not None:
            body = json.dumps(data)
            headers = [('Content-Length', len(body))]
            content_type = 'application/json'
        return http.Response(body, status=status, headers=headers,
                             content_type=content_type)

    def dispatch(self):
        r = self._call_function(**self.params)
        # For convenience, we handle by default
        # some common return formats that REST handlers may use
        # if already a Response instance, just return it
        if isinstance(r, http.Response):
            return r
        # if a tuple, assume it's (status_code, json_data)
        if type(r) == tuple:
            return self.json_response(status=r[0], data=r[1])
        # if just an integer, assume it's the status code
        if type(r) == int:
            return self.json_response(status=r)
        # In any other case (mainly dict and list), assume it's the json
        # data and return it with status 200
        return self.json_response(data=r)

original_get_request = http.Root.get_request

def get_request(self, httprequest):
    # Odoo "catches" json requests as json-rpc
    # To avoid that, first we check if the request matches one of the
    # endpoints registered as REST. If it does, we return
    # a RESTRequest; if it doesn't we let the original implementation
    # handle it.
    with http.WebRequest(httprequest) as request:
        endpoint, _ = request.env['ir.http']._find_handler()
        if endpoint.routing.get('subtype') == 'rest':
            return RESTRequest(httprequest)
    return original_get_request(self, httprequest)

def patch():
    http.Root.get_request = get_request

def unpatch():
    http.Root.get_request = original_get_request

patch()
