from typing import Generic
from typing import List
from typing import Literal
from typing import TypeVar

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


T = TypeVar("T")


class ActionParam(BaseModel):
    name: str
    kind: Literal["text_param"] = "text_param"
    value: str | None = None


class Action(BaseModel):
    kind: Literal["question_action"]
    params: List[ActionParam]


class Card(Generic[T], BaseModel):
    kind: str
    rows: List[T]


class TextCard(Card[str]):
    kind: Literal["text_card"] = "text_card"
    rows: List[str]


class ActionCard(Card[Action]):
    kind: Literal["action_card"] = "action_card"
    rows: list[Action]


class QuestionAction(Action):
    kind: Literal["question_action"] = "question_action"
    params: list[ActionParam] = [ActionParam(name="question", kind="text_param")]


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
