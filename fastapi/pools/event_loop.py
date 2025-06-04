# Copyright 2025 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/LGPL).

import asyncio
import queue
import threading
from collections.abc import Generator
from contextlib import contextmanager


class EventLoopPool:
    def __init__(self):
        self.pool = queue.Queue[tuple[asyncio.AbstractEventLoop, threading.Thread]]()

    def __get_event_loop_and_thread(
        self,
    ) -> tuple[asyncio.AbstractEventLoop, threading.Thread]:
        """
        Get an event loop from the pool. If no event loop is available,
        create a new one.
        """
        try:
            return self.pool.get_nowait()
        except queue.Empty:
            loop = asyncio.new_event_loop()
            thread = threading.Thread(target=loop.run_forever, daemon=True)
            thread.start()
            return loop, thread

    def __return_event_loop(
        self, loop: asyncio.AbstractEventLoop, thread: threading.Thread
    ) -> None:
        """
        Return an event loop to the pool for reuse.
        """
        self.pool.put((loop, thread))

    def shutdown(self):
        """
        Shutdown all event loop threads in the pool.
        """
        while not self.pool.empty():
            loop, thread = self.pool.get_nowait()
            loop.call_soon_threadsafe(loop.stop)
            thread.join()
            loop.close()

    @contextmanager
    def get_event_loop(self) -> Generator[asyncio.AbstractEventLoop, None, None]:
        """
        Get an event loop from the pool. If no event loop is available,
        create a new one.

        After the context manager exits, the event loop is returned to
        the pool for reuse.
        """
        loop, thread = self.__get_event_loop_and_thread()
        try:
            yield loop
        finally:
            self.__return_event_loop(loop, thread)
