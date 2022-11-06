from pydantic import BaseModel
from structlog import get_logger

from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.cards.all import CARD_TYPE_UNION
from ice.kelvin.cards.text import TextCard
from ice.kelvin.utils import generate_id
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView

log = get_logger()


class Workspace(BaseModel):
    cards: list[CARD_TYPE_UNION]
    view: CardView
    available_actions: list[Action]


def get_initial_workspace() -> Workspace:
    initial_card_id = generate_id()
    initial_card = TextCard(
        id=initial_card_id,
        rows=[],
    )
    initial_view = CardView(
        card_id=initial_card_id,
        selected_rows={},
        focused_row_index=None,
    )
    return Workspace(
        cards=[initial_card],
        view=initial_view,
        available_actions=get_available_actions(
            card_with_view=CardWithView(card=initial_card, view=initial_view)
        ),
    )
