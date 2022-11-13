from typing import Literal

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.text import TextCard
from ice.kelvin.utils import generate_id
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView


def clear_card_with_view() -> CardWithView:
    card_id = generate_id()
    card = TextCard(
        id=card_id,
        rows=[],
    )
    view = CardView(
        card_id=card_id,
        selected_rows={},
        focused_row_index=None,
    )
    return CardWithView(card=card, view=view)


class ClearAction(Action):

    kind: Literal["ClearAction"] = "ClearAction"
    params: list[ActionParam] = []
    label: str = "Clear card"

    def validate_input(self, card: Card) -> None:
        pass

    def execute(self, card: Card) -> CardWithView:
        return clear_card_with_view()

    @classmethod
    def instantiate(cls, card_with_view: CardWithView) -> list[Action]:
        if card_with_view.card.rows:
            return [cls(prev_id=card_with_view.card.id)]
        return []
