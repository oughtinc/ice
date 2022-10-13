from fastapi import APIRouter

from ice.agent import MACHINE_AGENTS
from ice.routes.base import RouteModel

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/list")
async def apiList():
    return list(MACHINE_AGENTS.keys())


class CompleteRequest(RouteModel):
    agent: str
    prompt: str
    multiline: bool


@router.post("/complete")
async def complete(request: CompleteRequest):
    if request.agent not in MACHINE_AGENTS:
        return "Invalid agent!"
    completionAgent = MACHINE_AGENTS[request.agent]()
    result = await completionAgent.complete(
        prompt=request.prompt, stop=None if request.multiline else "\n"
    )
    return result
