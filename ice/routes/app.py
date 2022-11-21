from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse

from ice.routes import agents
from ice.routes import traces
from ice.trace import trace_dir

dist_dir = Path(__file__).parent.parent.parent / "ui" / "dist"

app = FastAPI()
app.include_router(agents.router)
app.include_router(traces.router)
app.mount(
    "/api/traces/", StaticFiles(directory=trace_dir), name="static"
)  # see comment on get_trace
app.mount("/assets/", StaticFiles(directory=dist_dir / "assets"), name="static")


@app.get("/{_full_path:path}")
async def catch_all(_full_path: str):
    return FileResponse(dist_dir / "index.html")
