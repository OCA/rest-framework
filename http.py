import collections
import logging
import json
import werkzeug.exceptions

from odoo import http
from odoo.exceptions import ValidationError, MissingError


_logger = logging.getLogger(__name__)


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
        self.body = None
        raw_body = (
            self.httprequest.stream.read()
            if self.httprequest.method in ('POST', 'PUT')
            else None)
        if raw_body:
            try:
                self.body = json.loads(raw_body)
            except ValueError:
                msg = 'Invalid JSON data: %r' % (raw_body,)
                _logger.error('%s: %s', self.httprequest.path, msg)
                raise werkzeug.exceptions.BadRequest(msg)
        params = collections.OrderedDict(self.httprequest.args)
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

    def success(self, data=None, http_code=200):
        return self.json_response(
            http_code, {'status': 'success', 'data': data})

    def fail(self, error_data, http_code=400):
        return self.json_response(
            http_code, {
                'status': 'fail',
                'data': error_data,
            }
        )

    def error(self, exception, http_code=500):
        return self.json_response(
            http_code, {
                'status': 'error',
                'message': '{}: {}'.format(
                    exception.__class__.__name__, exception)
            }
        )

    def _handle_exception(self, exception):
        import pdb
        pdb.set_trace()
        print exception
        try:
            super(RESTRequest, self)._handle_exception(exception)
        except Exception:
            if isinstance(exception, ValidationError):
                return self.fail({
                    'code': 'validation-error',
                    'reason': 'Invalid parameter value',
                    'message': exception.name,
                })
            if isinstance(exception, MissingError):
                return self.fail({
                    'reason': 'Missing Record',
                    'code': 'no-such-record',
                    'message': exception.name
                }, 404)
            return self.error(exception)

    def dispatch(self):
        r = self._call_function(**self.params)
        # For convenience, we handle by default
        # some common return formats that REST handlers may use
        # if already a Response instance, just return it
        if isinstance(r, http.Response):
            return r
        # if a tuple, assume it's (status_code, json_data)
        if type(r) == tuple:
            return self.success(data=r[1], http_code=r[0])
        # if just an integer, assume it's the status code
        if type(r) == int:
            return self.success(http_code=r)
        # In any other case (mainly dict and list), assume it's the json
        # data and return it with status 200
        return self.success(data=r)

original_get_request = http.Root.get_request

def get_request(self, httprequest):
    # Odoo "catches" json requests as json-rpc
    # To avoid that, first we check if the request matches one of the
    # endpoints registered as REST. If it does, we return
    # a RESTRequest; if it doesn't we let the original implementation
    # handle it.
    with http.WebRequest(httprequest) as request:
        if not request.db:
            return original_get_request(self, httprequest)
        try:
            endpoint, _ = request.env['ir.http']._find_handler()
        except werkzeug.exceptions.NotFound:
            return original_get_request(self, httprequest)
        if endpoint.routing.get('subtype') == 'rest':
            return RESTRequest(httprequest)
    return original_get_request(self, httprequest)

def patch():
    http.Root.get_request = get_request

def unpatch():
    http.Root.get_request = original_get_request

patch()
