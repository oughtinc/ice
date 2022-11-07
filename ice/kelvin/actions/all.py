from typing import cast

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.clear import ClearAction
from ice.kelvin.actions.elicit import VespaSearchAction
from ice.kelvin.actions.lm import GenerationAction
from ice.kelvin.actions.text import AddTextRowAction
from ice.kelvin.actions.text import EditTextRowAction
from ice.kelvin.view import CardWithView


ACTION_TYPE_UNION = (
    AddTextRowAction
    | EditTextRowAction
    | GenerationAction
    | VespaSearchAction
    | ClearAction
)
ACTION_CLASSES = [
    AddTextRowAction,
    EditTextRowAction,
    GenerationAction,
    VespaSearchAction,
    ClearAction,
]


def get_available_actions(card_with_view: CardWithView) -> list[Action]:
    available_actions: list[Action] = []
    for action_class in ACTION_CLASSES:
        available_actions += cast(Action, action_class).instantiate(card_with_view)
    return available_actions
