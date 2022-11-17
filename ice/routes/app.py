from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from ice.routes import agents, traces
from ice.trace import trace_dir

app = FastAPI()
app.include_router(agents.router)
app.include_router(traces.router)
app.mount("/api/traces/", StaticFiles(directory=trace_dir), name="static")
