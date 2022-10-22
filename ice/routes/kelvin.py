from typing import Generic
from typing import List
from typing import Literal
from typing import TypeVar

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


T = TypeVar("T")


class Card(Generic[T], BaseModel):
    rows: List[T]


class TextCard(Card[str]):
    pass


class Action(BaseModel):
    action_type: Literal["ask_question"]
    action_param_types: dict
    action_param_values: dict


class QuestionAction(Action):
    action_type: Literal["ask_question"] = "ask_question"
    action_param_types: dict = {"question": "text"}
    action_param_values: dict = {}


class ActionCard(Card[Action]):
    pass


class Workspace(BaseModel):
    cards: dict[str, Card]
    currentCardId: str


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    return Workspace(
        cards={
            "initial": ActionCard(rows=[QuestionAction()]),
        },
        currentCardId="initial",
    )
