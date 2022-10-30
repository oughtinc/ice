from typing import Literal

from pydantic import Field

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.text import TextCard
from ice.kelvin.cards.text import TextRow
from ice.kelvin.utils import generate_id
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView


class AddTextRowAction(Action):
    """An action that adds a new text row to a text card."""

    kind: Literal["AddTextRowAction"] = "AddTextRowAction"
    params: list[ActionParam] = [
        ActionParam(name="row_text", kind="TextParam", label="Text")
    ]
    label: str = "Add bullet"

    def validate_input(self, card: Card) -> None:
        """Check that the card kind is TextCard."""
        if not card.kind == "TextCard":
            raise ValueError(
                f"Unsupported card kind for AddTextRowAction: {card.kind}",
            )

    def execute(self, card: Card) -> CardWithView:
        """Create a new text card with the added row and return it with a new view."""
        new_row_text = self.params[0].value
        new_card_id = generate_id()
        new_row = TextRow(text=new_row_text)
        new_card = TextCard(id=new_card_id, rows=card.rows + [new_row])
        new_view = CardView(
            card_id=new_card_id,
            selected_rows={},
        )

        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card: Card, selected_rows: dict[str, bool]) -> list[Action]:
        if not card.kind == "TextCard":
            return []
        return [cls()]


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

    def validate_input(self, card: Card) -> None:
        """Check that the card kind is TextCard and the row_id is valid."""
        if not card.kind == "TextCard":
            raise ValueError(
                f"Unsupported card kind for EditTextRowAction: {card.kind}",
            )
        row_id = self.params[1].value
        if row_id not in {row["id"] for row in card.rows}:
            raise ValueError(f"Invalid row id: {row_id}")

    def execute(self, card: Card) -> CardWithView:
        """Create a new text card with the edited row and return it with a new view."""
        new_row_text = self.params[0].value
        row_id = self.params[1].value

        new_rows = [
            TextRow(
                id=row["id"], text=new_row_text if row["id"] == row_id else row["text"]
            )
            for row in card.rows
        ]

        new_card = TextCard(id=generate_id(), rows=new_rows)

        new_view = CardView(
            card_id=new_card.id,
            selected_rows={},
        )

        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card: Card, selected_rows: dict[str, bool]) -> list[Action]:
        if not card.kind == "TextCard":
            return []
        actions: list[Action] = []
        for (selected_row_id, is_selected) in selected_rows.items():
            if not is_selected:
                continue
            rows = card.rows
            row = next(
                (row for i, row in enumerate(rows) if row["id"] == selected_row_id),
                None,
            )
            if row is None:
                raise ValueError(f"Row id {selected_row_id} not found")
            previous_text = row["text"]
            # truncate the previous text and add ellipsis if longer than 20 characters
            truncated_text = previous_text[:20] + (
                "..." if len(previous_text) > 20 else ""
            )
            actions.append(
                cls(
                    params=[
                        ActionParam(
                            name="new_row_text", kind="TextParam", label="New text"
                        ),
                        ActionParam(
                            name="row_id",
                            kind="IdParam",
                            value=selected_row_id,
                            label="Text Id",
                        ),
                    ],
                    label=f'Edit text "{truncated_text}"',
                )
            )
        return actions
