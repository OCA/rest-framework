from .event_loop import EventLoopPool
from .fastapi_app import FastApiAppPool
from odoo.service.server import CommonServer

event_loop_pool = EventLoopPool()
fastapi_app_pool = FastApiAppPool()


CommonServer.on_stop(event_loop_pool.shutdown)

__all__ = ["event_loop_pool", "fastapi_app_pool"]
