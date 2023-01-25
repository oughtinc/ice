import logging
import os
import re
import signal

from collections.abc import Awaitable
from collections.abc import Callable
from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import FileResponse
from starlette.responses import PlainTextResponse

from ice.routes import traces
from ice.trace import traces_dir

logger = logging.getLogger(__name__)

dist_dir = Path(__file__).parent / "ui"


app = FastAPI()


# Add cache-control: no-transform header to all responses
# because otherwise cloudflare brotli compression breaks the trace viewer
async def add_no_transform_header(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
):
    response = await call_next(request)
    response.headers.update({"cache-control": "no-transform"})
    return response


app.add_middleware(BaseHTTPMiddleware, dispatch=add_no_transform_header)

app.include_router(traces.router)
app.mount(
    "/api/traces/", StaticFiles(directory=traces_dir), name="static"
)  # see comment on get_trace

try:
    app.mount("/assets/", StaticFiles(directory=dist_dir / "assets"), name="static")
except RuntimeError:
    logger.warning(
        "ui folder not found, skipping static file mount. Run `npm run build` to build the ui."
    )


PING_RESPONSE = "ought-ice says pong"


@app.get("/ping")
async def ping():
    return PlainTextResponse(PING_RESPONSE)


@app.post("/stop")
async def stop():
    # Note that this doesn't work properly when the server runs with --reload
    os.kill(os.getpid(), signal.SIGKILL)


@app.get("/{path:path}")
async def catch_all(path: str):
    # Never serve index.html for API requests or assets
    if re.match(r"^(?:api|assets)(?:/.*)?$", path):
        return PlainTextResponse("404 File Not Found", status_code=404)

    index_path = dist_dir / "index.html"
    if not index_path.exists():
        return PlainTextResponse(
            "ui/index.html not found. Run `npm run build` in the ui directory to create it, "
            "or run `npm run dev` to run the dev server and access localhost:5173 instead.",
            status_code=500,
        )

    return FileResponse(index_path)
