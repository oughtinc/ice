from fastapi import APIRouter
from fastapi import Depends

from ice.agent import MACHINE_AGENTS
from ice.routes.auth import check_auth
from ice.routes.base import RouteModel

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/list", response_model=list[str])
async def get_list():
    return list(MACHINE_AGENTS.keys())


class CompleteRequest(RouteModel):
    agent: str
    prompt: str
    multiline: bool


@router.post("/complete", response_model=str, dependencies=[Depends(check_auth)])
async def complete(request: CompleteRequest):
    if request.agent not in MACHINE_AGENTS:
        return "Invalid agent!"
    completionAgent = MACHINE_AGENTS[request.agent]()
    result = await completionAgent.complete(
        prompt=request.prompt, stop=None if request.multiline else "\n"
    )
    return result


class classifyRequest(RouteModel):
    agent: str
    prompt: str
    options: list[str]


@router.post(
    "/classify", response_model=dict[str, float], dependencies=[Depends(check_auth)]
)
async def classify(request: classifyRequest):
    if request.agent not in MACHINE_AGENTS:
        return "Invalid agent!"
    classifyAgent = MACHINE_AGENTS[request.agent]()
    result = await classifyAgent.classify(
        prompt=request.prompt, choices=tuple(request.options)
    )
    return result[0]
