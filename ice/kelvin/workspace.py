from pydantic import BaseModel

from ice.kelvin.actions.all import get_available_actions
from ice.kelvin.actions.base import Action
from ice.kelvin.models import Card
from ice.kelvin.models import CardId
from ice.kelvin.models import Frontier
from ice.kelvin.models import Path
from ice.kelvin.models import PathId


class Workspace(BaseModel):
    cards: dict[CardId, Card]
    paths: dict[PathId, Path]
    focus_path_id: PathId
    available_actions: list[Action]

    def frontier(self) -> Frontier:
        return Frontier(
            paths={
                path_id: path.hydrate(self.cards)
                for path_id, path in self.paths.items()
            },
            focus_path_id=self.focus_path_id,
        )

    @classmethod
    def get_initial(cls) -> "Workspace":
        initial_card = Card()
        initial_cards = {initial_card.id: initial_card}
        initial_path = Path(
            label="Main",
            head_card_id=initial_card.id,
        )
        initial_frontier = Frontier(
            paths={initial_path.id: initial_path.hydrate(initial_cards)},
            focus_path_id=initial_path.id,
        )
        initial_actions = get_available_actions(initial_frontier)
        return cls(
            cards=initial_cards,
            paths={initial_path.id: initial_path},
            focus_path_id=initial_path.id,
            available_actions=initial_actions,
        )
