"""
Types:

A row is:
- An id
- A kind (string / enum)
- Some content (varies by row type)

A path is:
- An id
- A label (string)
- A pointer to a head card (card id)
- A view

A card is:
- An id
- A list of rows
- Pointers to successor and predecessor cards.

The workspace is:
- A map from card ids to cards
- A map from path ids to paths
- A focused path id
- (A set of currently available actions)

A view is:
- A set of selected rows
- A focused row index

A hydrated path is:
- An id
- A label
- A head card
- A view

A frontier is:
- A map from path id to hydrated path
- A focused path id


Function interfaces:

action.execute: Frontier -> Frontier

action.instantiate: Frontier -> list[Action]
"""
from typing import Any

from pydantic import BaseModel
from pydantic import Field

from ice.kelvin.rows import Row
from ice.kelvin.rows import ROW_TYPE_UNION
from ice.kelvin.rows import RowId
from ice.kelvin.utils import generate_id

CardId = str
PathId = str


class Card(BaseModel):
    id: CardId = Field(default_factory=generate_id)
    rows: list[ROW_TYPE_UNION] = Field(default_factory=list)
    next_id: CardId | None = None
    prev_id: CardId | None = None
    created_by_action: Any = None

    def __str__(self):
        rows_str = "\n".join([str(row) for row in self.rows])
        if not rows_str and not self.prev_id and not self.created_by_action:
            # This is the root card.
            return f"""<card id="{self.id}">(Initial card)</card>"""
        return f"""<card id="{self.id}">
{rows_str}
</card>"""


class View(BaseModel):
    selected_row_ids: dict[RowId, bool] = Field(default_factory=dict)
    focused_row_index: int | None = None


class Path(BaseModel):
    id: PathId = Field(default_factory=generate_id)
    label: str
    head_card_id: CardId
    view: View = View()

    def hydrate(self, cards: dict[CardId, Card]) -> "HydratedPath":
        return HydratedPath(
            id=self.id,
            label=self.label,
            head_card=cards[self.head_card_id],
            view=self.view,
        )


class HydratedPath(BaseModel):
    id: PathId
    label: str
    head_card: Card
    view: View

    def rows(self) -> list[Row]:
        return self.head_card.rows

    def get_marked_rows(self) -> list[Row]:
        """
        Return rows that are either selected or focused.
        """
        return [
            row
            for i, row in enumerate(self.rows())
            if self.view.selected_row_ids.get(row.id)
            or i == self.view.focused_row_index
        ]

    def get_marked_row_kinds(self) -> set[str]:
        return {row.kind for row in self.get_marked_rows()}

    def update_head(
        self, new_head_card: Card, new_view: View | None = None
    ) -> "HydratedPath":
        return HydratedPath(
            id=self.id,
            label=self.label,
            head_card=new_head_card,
            view=self.view if new_view is None else new_view,
        )


class Frontier(BaseModel):
    paths: dict[PathId, HydratedPath]
    focus_path_id: PathId

    def focus_path(self) -> HydratedPath:
        return self.paths[self.focus_path_id]

    def update_focus_path(self, new_focus_path: HydratedPath) -> "Frontier":
        return Frontier(
            paths={**self.paths, new_focus_path.id: new_focus_path},
            focus_path_id=new_focus_path.id,
        )

    def focus_path_head(self) -> Card:
        return self.focus_path().head_card

    def update_focus_path_head(
        self, new_head_card: Card, new_view: View | None = None
    ) -> "Frontier":
        return self.update_focus_path(
            self.focus_path().update_head(new_head_card, new_view)
        )

    def get_marked_rows(self) -> list[Row]:
        return self.focus_path().get_marked_rows()

    def get_marked_row_kinds(self) -> set[str]:
        return self.focus_path().get_marked_row_kinds()


# Same as Frontier, but used to signpost places where we might not
# return a full replacement, i.e. paths will only include paths that
# are being modified.
PartialFrontier = Frontier
