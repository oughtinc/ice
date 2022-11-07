from pydantic import BaseModel
from structlog import get_logger

from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.actions.clear import clear_card_with_view
from ice.kelvin.cards.all import CARD_TYPE_UNION
from ice.kelvin.view import CardView

log = get_logger()


class Workspace(BaseModel):
    cards: list[CARD_TYPE_UNION]
    view: CardView
    available_actions: list[Action]


def get_initial_workspace() -> Workspace:
    cleared = clear_card_with_view()
    return Workspace(
        cards=[cleared.card],
        view=cleared.view,
        available_actions=get_available_actions(card_with_view=cleared),
    )
