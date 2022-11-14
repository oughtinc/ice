from typing import Literal

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.models import Card
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.models import View


class ClearAction(Action):

    kind: Literal["ClearAction"] = "ClearAction"
    params: list[ActionParam] = []
    label: str = "Clear card"

    def execute(self, frontier: Frontier) -> PartialFrontier:
        prev_card = frontier.focus_path_head()
        clear_card = Card(prev_id=prev_card.id)
        new_frontier = frontier.update_focus_path_head(
            new_head_card=clear_card,
            new_view=View(),
        )
        return new_frontier

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        if frontier.focus_path().rows():
            return [cls()]
        return []
