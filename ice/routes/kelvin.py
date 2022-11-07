from fastapi import APIRouter
from fastapi import HTTPException
from structlog import get_logger

from ice.kelvin.actions.all import ACTION_TYPE_UNION
from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.cards.all import CARD_TYPE_UNION
from ice.kelvin.view import CardWithView
from ice.kelvin.workspace import get_initial_workspace
from ice.kelvin.workspace import Workspace

log = get_logger()

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


@router.get("/hello/", response_model=str)
async def hello_world():
    return "Hello World"


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    return get_initial_workspace()


@router.post("/actions/execute", response_model=CardWithView)
async def execute_action(action: ACTION_TYPE_UNION, card: CARD_TYPE_UNION):
    log.info("execute_action", action=action, card=card)
    try:
        action.validate_input(card)
    except ValueError:
        raise HTTPException(
            400, detail=f"Couldn't validate input for action {action.kind}"
        )
    return action.execute(card)


@router.post("/actions/available", response_model=list[Action])
async def available_actions(card_with_view: CardWithView):
    return get_available_actions(card_with_view)
