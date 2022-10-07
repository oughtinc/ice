from fastapi import APIRouter

from ice.routes.base import RouteModel

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/list")
async def list():
    return ["alice", "bob"]


class CompleteRequest(RouteModel):
    prompt: str


@router.post("/complete")
async def complete(request: CompleteRequest):
    return "hi"
