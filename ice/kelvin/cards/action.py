from typing import Literal

from ice.kelvin.actions.base import Action
from ice.kelvin.cards.base import Card


class ActionCard(Card[Action]):
    kind: Literal["ActionCard"] = "ActionCard"
    rows: list[Action]
