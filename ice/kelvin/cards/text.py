from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ice.kelvin.cards.base import Card
from ice.kelvin.utils import generate_id


class TextRow(BaseModel):
    text: str
    id: str = Field(default_factory=generate_id)


class TextCard(Card[TextRow]):
    kind: Literal["TextCard"] = "TextCard"
    rows: list[TextRow]
