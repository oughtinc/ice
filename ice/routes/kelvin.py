from typing import List, TypeVar, Generic
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


T = TypeVar("T")


class Card(Generic[T], BaseModel):
    rows: List[T]


class TextCard(Card[str]):
    pass


class Action(BaseModel):
    name: str
    params: dict


class ActionCard(Card[Action]):
    pass


class Workspace(BaseModel):
    cards: dict[str, Card]
    currentCardId: str


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    return Workspace(
        cards={
            "initial": TextCard(rows=["one", "two"]),
        },
        currentCardId="initial",
    )
