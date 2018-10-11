import logging

from odoo import http

API_PREFIX = '/api/v1'
_logger = logging.getLogger(__name__)


def restroute(endpoint, force_multi=False, force_single=False, **kwargs):
    """
    Utility decorator for REST endpoints.

    This decorator calls the standard http.route decorator with some
    params already defined:

    * subtype='rest'
    * auth='public'
    * Prepend API_PREFIX to the endpoint path
    """
    if force_multi and force_single:
        _logger.error(
            'Route %s defined with both force_single and force_multi',
            endpoint)
    return http.route(
        '{}{}'.format(API_PREFIX, endpoint),
        subtype='rest',
        auth='public',
        force_multi=force_multi,
        force_single=force_single,
        **kwargs
    )

def restroutemulti(endpoint, **kwargs):
    return restroute(endpoint, force_multi=True, **kwargs)

def restroutesingle(endpoint, **kwargs):
    return restroute(endpoint, force_single=True, **kwargs)