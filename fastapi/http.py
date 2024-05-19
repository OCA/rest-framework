# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

from functools import lru_cache

import odoo
from odoo import http


class FastapiRootPaths:
    _root_paths_by_db = {}

    @classmethod
    def set_root_paths(cls, db, root_paths):
        cls._root_paths_by_db[db] = root_paths
        cls.is_fastapi_path.cache_clear()

    @classmethod
    @lru_cache(maxsize=1024)
    def is_fastapi_path(cls, db, path):
        return any(
            path.startswith(root_path)
            for root_path in cls._root_paths_by_db.get(db, [])
        )


class HttpFastapiRequest(http.HttpRequest):
    _request_type = "fastapi"


ori_get_request = http.root.__class__.get_request


def get_request(self, httprequest):
    db = httprequest.session.db
    if db and odoo.service.db.exp_db_exist(db):
        # on the very first request processed by a worker,
        # registry is not loaded yet
        # so we enforce its loading here.
        odoo.registry(db)
        if FastapiRootPaths.is_fastapi_path(db, httprequest.path):
            return HttpFastapiRequest(httprequest)
    return ori_get_request(self, httprequest)


http.root.__class__.get_request = get_request
