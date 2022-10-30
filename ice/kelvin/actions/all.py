from typing import cast

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.elicit import ElicitSearchAction
from ice.kelvin.actions.text import AddTextRowAction
from ice.kelvin.actions.text import EditTextRowAction
from ice.kelvin.cards.base import Card
from ice.kelvin.view import CardView


ACTION_TYPE_UNION = AddTextRowAction | EditTextRowAction | ElicitSearchAction
ACTION_CLASSES = [AddTextRowAction, EditTextRowAction, ElicitSearchAction]


def get_available_actions(card: Card, view: CardView) -> list[Action]:
    available_actions: list[Action] = []
    for action_class in ACTION_CLASSES:
        available_actions += cast(Action, action_class).instantiate(
            card, view.selected_rows
        )
    return available_actions
