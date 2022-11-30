import logging
import os
import signal

from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.responses import PlainTextResponse

from ice.routes import traces
from ice.settings import server_url
from ice.trace import traces_dir

logger = logging.getLogger(__name__)

dist_dir = Path(__file__).parent / "ui"

app = FastAPI()
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


def is_server_running():
    try:
        response = httpx.get(server_url() + "/ping")
        return response.text == PING_RESPONSE
    except httpx.HTTPError:
        return False


@app.post("/stop")
async def stop():
    # Note that this doesn't work properly when the server runs with --reload
    os.kill(os.getpid(), signal.SIGKILL)


@app.get("/{_full_path:path}")
async def catch_all(_full_path: str):
    path = dist_dir / "index.html"
    if not path.exists():
        return PlainTextResponse(
            "ui/index.html not found. Run `npm run build` in the ui directory to create it, "
            "or run `npm run dev` to run the dev server and access localhost:5173 instead."
        )
    return FileResponse(path)
