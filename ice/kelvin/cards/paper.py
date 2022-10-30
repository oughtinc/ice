from typing import Literal

from pydantic import Field

from ice.kelvin.cards.base import Card
from ice.kelvin.cards.base import CardRow
from ice.kelvin.utils import generate_id


class PaperRow(CardRow):
    id: str = Field(default_factory=generate_id)
    title: str | None
    authors: list[str]
    year: int | None
    citations: int | None
    raw_data: dict


class PaperCard(Card):
    id: str = Field(default_factory=generate_id)
    kind: Literal["PaperCard"] = "PaperCard"
    rows: list[PaperRow]
