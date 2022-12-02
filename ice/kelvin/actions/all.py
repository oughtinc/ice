from typing import cast

from structlog import get_logger

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.clear import ClearAction
from ice.kelvin.actions.elicit import ElicitSearchAction
from ice.kelvin.actions.elicit import ViewPaperAction
from ice.kelvin.actions.expand_collapse import ToggleAction
from ice.kelvin.actions.lm import GenerationAction
from ice.kelvin.actions.model_action import get_model_actions
from ice.kelvin.actions.path import CreatePathAction
from ice.kelvin.actions.path import SaveElementToPathAction
from ice.kelvin.actions.path import SwitchPathAction
from ice.kelvin.actions.text import AddTextRowAction
from ice.kelvin.actions.text import EditTextRowAction
from ice.kelvin.history import History
from ice.kelvin.models import Frontier

# from ice.kelvin.actions.elicit import VespaSearchAction


log = get_logger()

ACTION_TYPE_UNION = (
    AddTextRowAction
    | EditTextRowAction
    | GenerationAction
    | ElicitSearchAction
    # | VespaSearchAction
    | ViewPaperAction
    | ToggleAction
    | SaveElementToPathAction
    | ClearAction
    | SwitchPathAction
    | CreatePathAction
)
ACTION_CLASSES = [
    AddTextRowAction,
    EditTextRowAction,
    GenerationAction,
    ElicitSearchAction,
    # VespaSearchAction,
    ViewPaperAction,
    ToggleAction,
    SaveElementToPathAction,
    ClearAction,
    SwitchPathAction,
    CreatePathAction,
]


def get_available_actions(frontier: Frontier, history: History) -> list[Action]:
    available_actions: list[Action] = []
    for action_class in ACTION_CLASSES:
        available_actions += cast(Action, action_class).instantiate(frontier)
    # if len(history) > 1:
    #     model_actions = get_model_actions(frontier, history)
    #     available_actions = [model_actions[0]] + available_actions + model_actions[1:]
    return available_actions
