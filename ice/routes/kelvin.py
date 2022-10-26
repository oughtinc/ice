import random
import string

from typing import Generic
from typing import List
from typing import Literal
from typing import TypeVar

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/kelvin", tags=["kelvin"])


def generate_card_id():
    """
    Generate a random card id of 8 alphanumeric characters
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


T = TypeVar("T")


class ActionParam(BaseModel):
    name: str
    kind: Literal["text_param"] = "text_param"
    value: str | None = None


class Action(BaseModel):
    kind: Literal["create_question_action"]
    params: List[ActionParam]


class Card(Generic[T], BaseModel):
    id: str
    kind: str
    rows: List[T]


class TextCard(Card[str]):
    kind: Literal["text_card"] = "text_card"
    rows: List[str]


class ActionCard(Card[Action]):
    kind: Literal["action_card"] = "action_card"
    rows: list[Action]


class QuestionAction(Action):
    kind: Literal["create_question_action"] = "create_question_action"
    params: list[ActionParam] = [ActionParam(name="question", kind="text_param")]


class Workspace(BaseModel):
    cards: list[Card]
    currentCardId: str


@router.get("/hello/", response_model=str)
async def hello_world():
    return "Hello World"


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    initial_card_id = generate_card_id()
    return Workspace(
        cards=[
            ActionCard(id=initial_card_id, rows=[QuestionAction()]),
        ],
        currentCardId=initial_card_id,
    )


@router.post("/workspaces/act", response_model=Workspace)
async def execute_action(workspace: Workspace, action: Action):
    if not action.kind == "create_question_action":
        raise HTTPException(
            status_code=400, detail=f"Unsupported action kind: {action.kind}"
        )

    # Get the question from the action params
    question = action.params[0].value
    # Generate a new card id
    new_card_id = generate_card_id()
    # Create a new text card with the question
    new_card = TextCard(id=new_card_id, rows=[question])
    # Add the new card to the workspace
    workspace.cards.append(new_card)
    # Update the current card id
    workspace.currentCardId = new_card_id
    return workspace
