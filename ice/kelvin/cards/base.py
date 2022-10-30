from typing import Generic
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Card(Generic[T], BaseModel):
    id: str
    kind: str
    rows: list[T]
