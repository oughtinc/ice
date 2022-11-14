from fastapi import APIRouter
from fastapi import HTTPException
from structlog import get_logger

from ice.kelvin.actions.all import ACTION_TYPE_UNION
from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.workspace import Workspace

log = get_logger()

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


@router.get("/hello/", response_model=str)
async def hello_world():
    return "Hello World"


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    return Workspace.get_initial()


@router.post("/actions/execute", response_model=PartialFrontier)
async def execute_action(action: ACTION_TYPE_UNION, frontier: Frontier):
    log.info("execute_action", action=action, frontier=frontier)
    try:
        action.validate_input(frontier)
    except ValueError:
        raise HTTPException(
            400, detail=f"Couldn't validate input for action {action.kind}"
        )
    return action.execute(frontier)


@router.post("/actions/available", response_model=list[Action])
async def available_actions(frontier: Frontier):
    return get_available_actions(frontier)
