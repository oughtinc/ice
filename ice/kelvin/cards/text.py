from typing import Literal

from pydantic import Field

from ice.kelvin.cards.base import Card
from ice.kelvin.cards.base import CardRow
from ice.kelvin.utils import generate_id


class TextRow(CardRow):
    id: str = Field(default_factory=generate_id)
    text: str


class TextCard(Card):
    id: str = Field(default_factory=generate_id)
    kind: Literal["TextCard"] = "TextCard"
    rows: list[TextRow]
