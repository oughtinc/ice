import asyncio

from pyee.asyncio import AsyncIOEventEmitter
from structlog import get_logger

from ice.logging import init_logging

init_logging()
log = get_logger()

try:
    loop = asyncio.get_running_loop()
except RuntimeError:
    # This can happen if we're initialising the app without FastAPI,
    # e.g. to carry out alembic migrations.
    loop = asyncio.new_event_loop()

events = AsyncIOEventEmitter(loop)
