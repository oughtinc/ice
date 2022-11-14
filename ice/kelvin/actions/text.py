from typing import cast
from typing import Literal

from pydantic import Field

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.models import Card
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.models import View
from ice.kelvin.rows import TextRow
from ice.kelvin.utils import truncate_text


class AddTextRowAction(Action):
    """An action that adds a new text row to a text card."""

    kind: Literal["AddTextRowAction"] = "AddTextRowAction"
    params: list[ActionParam] = [
        ActionParam(name="row_text", kind="TextParam", label="Text")
    ]
    label: str = "Add bullet point to card"

    def execute(self, frontier: Frontier) -> PartialFrontier:
        """Create a new text card with the added row and return it with a new view."""
        card = frontier.focus_path_head()
        new_row_text = self.params[0].value
        new_rows = card.rows + [TextRow(text=new_row_text)]
        new_card = Card(rows=new_rows, prev_id=card.id)
        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card,
            new_view=View(
                focused_row_index=len(new_rows) - 1,
            ),
        )
        return new_frontier

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        row_kinds = frontier.get_marked_row_kinds()
        if row_kinds in ({"Text"}, set()):
            return [cls()]
        return []


class EditTextRowAction(Action):
    """An action that edits the text of an existing row in a text card."""

    kind: Literal["EditTextRowAction"] = "EditTextRowAction"
    params: list[ActionParam] = Field(
        default_factory=lambda: [
            ActionParam(name="new_row_text", kind="TextParam", label="New text"),
            ActionParam(name="row_id", kind="IdParam", label="Text Id"),
        ]
    )
    label: str = "Edit text"

    def validate_input(self, frontier: Frontier) -> None:
        """Check that the row  id is in focus path head and is a text row."""
        row_id = self.params[1].value
        frontier_rows = frontier.focus_path_head().rows
        row_ids = {row.id for row in frontier_rows}
        if row_id not in row_ids:
            raise ValueError(f"Row id {row_id} not in focus path head")
        row_kinds = {row.kind for row in frontier_rows}
        if row_kinds != {"Text"}:
            raise ValueError(f"Row id {row_id} is not a text row")

    def execute(self, frontier: Frontier) -> PartialFrontier:
        """Create a new card with the edited row and return it."""
        card = frontier.focus_path_head()
        new_row_text = self.params[0].value
        row_id = self.params[1].value

        new_rows = [
            TextRow(id=row.id, text=new_row_text if row.id == row_id else row.text)
            for row in card.rows
        ]

        new_card = Card(rows=new_rows, prev_id=card.id)

        new_focused_row_index = next(
            (i for i, row in enumerate(new_rows) if row.id == row_id), None
        )

        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card,
            new_view=View(
                focused_row_index=new_focused_row_index,
            ),
        )
        return new_frontier

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        row_kinds = frontier.get_marked_row_kinds()
        if not row_kinds == {"Text"}:
            return []
        actions: list[Action] = []
        for row in frontier.get_marked_rows():
            previous_text = cast(TextRow, row).text
            truncated_text = truncate_text(previous_text, max_length=20)
            actions.append(
                cls(
                    params=[
                        ActionParam(
                            name="new_row_text",
                            kind="TextParam",
                            label="New text",
                            default_value=previous_text,
                        ),
                        ActionParam(
                            name="row_id",
                            kind="IdParam",
                            value=row.id,
                            label="Text Id",
                        ),
                    ],
                    label=f'Edit text "{truncated_text}"',
                )
            )
        return actions
