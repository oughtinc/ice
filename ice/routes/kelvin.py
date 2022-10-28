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
    kind: Literal["add_question_action"]
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


class AddQuestionAction(Action):
    kind: Literal["add_question_action"] = "add_question_action"
    params: list[ActionParam] = [ActionParam(name="question", kind="text_param")]


class CardView(BaseModel):
    card_id: str
    selected_row_index: int | None = None
    available_actions: List[Action]


class CardWithView(BaseModel):
    card: Card
    view: CardView


class Workspace(BaseModel):
    cards: list[Card]
    view: CardView


@router.get("/hello/", response_model=str)
async def hello_world():
    return "Hello World"


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    initial_card_id = generate_card_id()
    return Workspace(
        cards=[TextCard(id=initial_card_id, rows=[])],
        view=CardView(
            card_id=initial_card_id,
            selected_row_index=None,
            available_actions=[AddQuestionAction()],
        ),
    )


@router.post("/actions/execute", response_model=CardWithView)
async def execute_action(action: Action, card: Card):
    if not action.kind == "add_question_action":
        raise HTTPException(
            status_code=400, detail=f"Unsupported action kind: {action.kind}"
        )

    if not card.kind == "text_card":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported card kind for add_question_action: {card.kind}",
        )

    # Get the question from the action params
    question = action.params[0].value
    # Generate a new card id
    new_card_id = generate_card_id()
    # Create a new text card with the question
    new_card = TextCard(id=new_card_id, rows=card.rows + [question])
    # Create a new view for the new card
    new_view = CardView(
        card_id=new_card_id,
        selected_row_index=None,  # TODO
        available_actions=[AddQuestionAction()],  # TODO
    )

    # Return the new card and view
    return CardWithView(card=new_card, view=new_view)
