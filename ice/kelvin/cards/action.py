from typing import Literal

from pydantic import Field

from ice.kelvin.actions.base import Action
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.base import CardRow
from ice.kelvin.utils import generate_id


class ActionCardRow(CardRow):
    id: str = Field(default_factory=generate_id)
    action: Action


class ActionCard(Card):
    id: str = Field(default_factory=generate_id)
    kind: Literal["ActionCard"] = "ActionCard"
    rows: list[ActionCardRow]
