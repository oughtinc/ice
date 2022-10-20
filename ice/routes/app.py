from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ice.routes import agents
from ice.routes import kelvin

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(kelvin.router)
