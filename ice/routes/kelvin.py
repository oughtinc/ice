from typing import List
from pydantic import BaseModel

from fastapi import APIRouter

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


class Card(BaseModel):
    rows: list[str]


class Workspace(BaseModel):
    cards: dict[str, Card]
    currentCardId: str


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    return Workspace(
        cards={
            "initial": Card(rows=["one", "two"]),
        },
        currentCardId="initial",
    )
