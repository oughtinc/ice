from fastapi import FastAPI

from ice.routes import agents

app = FastAPI()
app.include_router(agents.router)
