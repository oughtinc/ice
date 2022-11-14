from typing import cast

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.clear import ClearAction
from ice.kelvin.actions.elicit import VespaSearchAction
from ice.kelvin.actions.elicit import ViewPaperAction
from ice.kelvin.actions.lm import GenerationAction
from ice.kelvin.actions.text import AddTextRowAction
from ice.kelvin.actions.text import EditTextRowAction
from ice.kelvin.models import Frontier


ACTION_TYPE_UNION = (
    AddTextRowAction
    | EditTextRowAction
    | GenerationAction
    | VespaSearchAction
    | ViewPaperAction
    | ClearAction
)
ACTION_CLASSES = [
    AddTextRowAction,
    EditTextRowAction,
    GenerationAction,
    VespaSearchAction,
    ViewPaperAction,
    ClearAction,
]


def get_available_actions(frontier: Frontier) -> list[Action]:
    available_actions: list[Action] = []
    for action_class in ACTION_CLASSES:
        available_actions += cast(Action, action_class).instantiate(frontier)
    return available_actions
