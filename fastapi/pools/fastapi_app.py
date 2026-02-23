# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).
import logging
import queue
import threading
from collections import defaultdict
from collections.abc import Generator
from contextlib import contextmanager

from odoo.api import Environment

from fastapi import FastAPI

_logger = logging.getLogger(__name__)


class FastApiAppPool:
    """Pool of FastAPI apps.

    This class manages a pool of FastAPI apps. The pool is organized by database name
    and root path. Each pool is a queue of FastAPI apps.

    The pool is used to reuse FastAPI apps across multiple requests. This is useful
    to avoid the overhead of creating a new FastAPI app for each request. The pool
    ensures that only one request at a time uses an app.

    The proper way to use the pool is to use the get_app method as a context manager.
    This ensures that the app is returned to the pool after the context manager exits.
    The get_app method is designed to ensure that the app made available to the
    caller is unique and not used by another caller at the same time.

    .. code-block:: python

        with fastapi_app_pool.get_app(env=request.env, root_path=root_path) as app:
            # use the app

    The pool is invalidated when the cache registry is updated. This ensures that
    the pool is always up-to-date with the latest app configuration. It also
    ensures that the invalidation is done even in the case of a modification occurring
    in a different worker process or thread or server instance. This mechanism
    works because every time an attribute of the fastapi.endpoint model is modified
    and this attribute is part of the list returned by the `_fastapi_app_fields`,
    or `_routing_impacting_fields` methods, we reset the cache of a marker method
    `_reset_app_cache_marker`. As side effect, the cache registry is marked to be
    updated by the increment of the `cache_sequence` SQL sequence.  This cache sequence
    on the registry is reloaded from the DB on each request made to a specific database.
    When an app is retrieved from the pool, we always compare the cache sequence of
    the pool with the cache sequence of the registry. If the two sequences are
    different, we invalidate the pool and save the new cache sequence on the pool.

    The cache is based on a defaultdict of defaultdict of queue.Queue. We are cautious
    that the use of defaultdict is not thread-safe for operations that modify the
    dictionary. However the only operation that modifies the dictionary is the
    first access to a new key. If two threads access the same key at the same time,
    the two threads will create two different queues. This is not a problem since
    at the time of returning an app to the pool, we are sure that a queue exists
    for the key into the cache and all the created apps are returned to the same
    valid queue. And the end, the lack of thread-safety for the defaultdict could
    only lead to a negligible overhead of creating a new queue that will never be
    used. This is why we consider that the use of defaultdict is safe in this context.
    """

    def __init__(self):
        self._queue_by_db_by_root_path: dict[str, dict[str, queue.Queue[FastAPI]]] = (
            defaultdict(lambda: defaultdict(queue.Queue))
        )
        self.__cache_sequences = {}
        self._lock = threading.Lock()

    def __get_pool(self, env: Environment, root_path: str) -> queue.Queue[FastAPI]:
        db_name = env.cr.dbname
        return self._queue_by_db_by_root_path[db_name][root_path]

    def __get_app(self, env: Environment, root_path: str) -> FastAPI:
        pool = self.__get_pool(env, root_path)
        try:
            return pool.get_nowait()
        except queue.Empty:
            return env["fastapi.endpoint"].sudo().get_app(root_path)

    def __return_app(self, env: Environment, app: FastAPI, root_path: str) -> None:
        pool = self.__get_pool(env, root_path)
        pool.put(app)

    @contextmanager
    def get_app(
        self, env: Environment, root_path: str
    ) -> Generator[FastAPI, None, None]:
        """Return a  FastAPI app to be used in a context manager.

        The app is retrieved from the pool if available, otherwise a new one is created.
        The app is returned to the pool after the context manager exits.

        When used into the FastApiDispatcher class this ensures that the app is reused
        across multiple requests but only one request at a time uses an app.
        """
        self._check_cache(env)
        app = self.__get_app(env, root_path)
        try:
            yield app
        finally:
            self.__return_app(env, app, root_path)

    def get_cache_sequence(self, key: str) -> int:
        with self._lock:
            return self.__cache_sequences.get(key, 0)

    def set_cache_sequence(self, key: str, value: int) -> None:
        with self._lock:
            if (
                key not in self.__cache_sequences
                or value != self.__cache_sequences[key]
            ):
                self.__cache_sequences[key] = value

    def _check_cache(self, env: Environment) -> None:
        cache_sequences = env.registry.cache_sequences
        for key, value in cache_sequences.items():
            if (
                value != self.get_cache_sequence(key)
                and self.get_cache_sequence(key) != 0
            ):
                _logger.info(
                    "Cache registry updated, reset fastapi_app pool for the current "
                    "database"
                )
                self.invalidate(env)
            self.set_cache_sequence(key, value)

    def invalidate(self, env: Environment, root_path: str | None = None) -> None:
        db_name = env.cr.dbname
        if root_path:
            self._queue_by_db_by_root_path[db_name][root_path] = queue.Queue()
        elif db_name in self._queue_by_db_by_root_path:
            del self._queue_by_db_by_root_path[db_name]
