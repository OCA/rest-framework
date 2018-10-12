import functools
import logging

from odoo import http


API_PREFIX = '/rest'
_logger = logging.getLogger(__name__)


def prepend_route_prefix(route):
    return '{}{}'.format(API_PREFIX, route)


def restroute(route=None, **kw):
    routing = kw.copy()
    routing['type'] = 'rest'

    if routing.get('force_multi') and routing.get('force_single'):
        _logger.error(
            'Route %s defined with both force_single and force_multi',
            route)
    def decorator(f):
        routing['routes'] = [
            prepend_route_prefix(r)
            for r in (route if isinstance(route, list) else [route])]
        print routing['routes']
        @functools.wraps(f)
        def response_wrap(*args, **kw):
            response = f(*args, **kw)
            return response
        response_wrap.routing = routing
        response_wrap.original_func = f
        return response_wrap
    return decorator


def restroutemulti(endpoint, **kwargs):
    return restroute(endpoint, force_multi=True, **kwargs)


def restroutesingle(endpoint, **kwargs):
    return restroute(endpoint, force_single=True, **kwargs)