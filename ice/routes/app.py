import logging

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse
from starlette.responses import PlainTextResponse

from ice.routes import agents
from ice.routes import traces
from ice.trace import trace_dir

logger = logging.getLogger(__name__)

dist_dir = Path(__file__).parent / "ui"

app = FastAPI()
app.include_router(agents.router)
app.include_router(traces.router)
app.mount(
    "/api/traces/", StaticFiles(directory=trace_dir), name="static"
)  # see comment on get_trace

try:
    app.mount("/assets/", StaticFiles(directory=dist_dir / "assets"), name="static")
except RuntimeError:
    logger.warning(
        "ui folder not found, skipping static file mount. Run `npm run build` to build the ui."
    )


@app.get("/{_full_path:path}")
async def catch_all(_full_path: str):
    path = dist_dir / "index.html"
    if not path.exists():
        return PlainTextResponse(
            "ui/index.html not found. Run `npm run build` in the ui directory to create it, "
            "or run `npm run dev` to run the dev server and access localhost:5173 instead."
        )
    return FileResponse(path)
