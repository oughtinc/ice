from pydantic import BaseModel
from structlog import get_logger

from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.text import TextCard
from ice.kelvin.cards.text import TextRow
from ice.kelvin.utils import generate_id
from ice.kelvin.view import CardView

log = get_logger()


class Workspace(BaseModel):
    cards: list[Card]
    view: CardView
    available_actions: list[Action]


def get_initial_workspace() -> Workspace:
    initial_card_id = generate_id()
    initial_card = TextCard(
        id=initial_card_id,
        rows=[TextRow(text="one"), TextRow(text="two"), TextRow(text="three")],
    )
    return Workspace(
        cards=[initial_card],
        view=CardView(
            card_id=initial_card_id,
            selected_rows={},
        ),
        available_actions=get_available_actions(card=initial_card, selected_rows={}),
    )
