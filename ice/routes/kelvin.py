from fastapi import APIRouter
from fastapi import HTTPException

from ice.kelvin.actions.all import ACTION_TYPE_UNION
from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.cards.base import Card
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView
from ice.kelvin.workspace import get_initial_workspace
from ice.kelvin.workspace import Workspace


router = APIRouter(prefix="/kelvin", tags=["kelvin"])


@router.get("/hello/", response_model=str)
async def hello_world():
    return "Hello World"


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    return get_initial_workspace()


# Action has two subclasses, Action1 and Action2
# Action has a "kind" attribute that distinguishes the subclasses


@router.post("/actions/execute", response_model=CardWithView)
async def execute_action(action: ACTION_TYPE_UNION, card: Card):
    try:
        action.validate_input(card)
    except ValueError:
        raise HTTPException(
            400, detail=f"Couldn't validate input for action {action.kind}"
        )
    return action.execute(card)


@router.post("/actions/available", response_model=list[Action])
async def available_actions(card: Card, view: CardView):
    return get_available_actions(card, view)
