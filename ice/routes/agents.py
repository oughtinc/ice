from fastapi import APIRouter
from fastapi import Depends
from pydantic import validator

from ice.agent import MACHINE_AGENTS
from ice.routes.auth import check_auth
from ice.routes.base import RouteModel

router = APIRouter(prefix="/agents", tags=["agents"])

class CompleteRequest(RouteModel):
    agent: str
    prompt: str
    stop: list[str]

    @validator('agent')
    def agent_must_exist(cls, v):
        if v not in MACHINE_AGENTS:
            raise ValueError('Invalid agent')
        return v

class classifyRequest(RouteModel):
    agent: str
    prompt: str
    options: list[str]

    @validator('agent')
    def agent_must_exist(cls, v):
        if v not in MACHINE_AGENTS:
            raise ValueError('Invalid agent')
        return v

@router.get("/list", response_model=list[str])
async def get_list():
    return list(MACHINE_AGENTS.keys())

@router.post("/complete", response_model=str, dependencies=[Depends(check_auth)])
async def complete(request: CompleteRequest):
    completionAgent = MACHINE_AGENTS[request.agent]()
    result = await completionAgent.complete(
        prompt=request.prompt, stop=request.stop if len(request.stop) else None
    )
    return result

@router.post(
    "/classify", response_model=dict[str, float], dependencies=[Depends(check_auth)]
)
async def classify(request: classifyRequest):
    classifyAgent = MACHINE_AGENTS[request.agent]()
    result = await classifyAgent.classify(
        prompt=request.prompt, choices=tuple(request.options)
    )
    return result[0]
