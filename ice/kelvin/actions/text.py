from typing import Literal

from pydantic import Field

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.text import TextCard
from ice.kelvin.cards.text import TextRow
from ice.kelvin.utils import generate_id
from ice.kelvin.utils import truncate_text
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView


class AddTextRowAction(Action):
    """An action that adds a new text row to a text card."""

    kind: Literal["AddTextRowAction"] = "AddTextRowAction"
    params: list[ActionParam] = [
        ActionParam(name="row_text", kind="TextParam", label="Text")
    ]
    label: str = "Add bullet point to card"

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
        new_card = TextCard(id=new_card_id, rows=card.rows + [new_row], prev_id=card.id)
        new_view = CardView(
            card_id=new_card_id,
            selected_rows={},
            focused_row_index=len(card.rows),
        )

        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card_with_view: CardWithView) -> list[Action]:
        if not card_with_view.card.kind == "TextCard":
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
        if row_id not in {row.id for row in card.rows}:
            raise ValueError(f"Invalid row id: {row_id}")

    def execute(self, card: Card) -> CardWithView:
        """Create a new text card with the edited row and return it with a new view."""
        new_row_text = self.params[0].value
        row_id = self.params[1].value

        new_rows = [
            TextRow(id=row.id, text=new_row_text if row.id == row_id else row.text)
            for row in card.rows
        ]

        new_card = TextCard(id=generate_id(), rows=new_rows, prev_id=card.id)

        new_focused_row_index = next(
            (i for i, row in enumerate(new_rows) if row.id == row_id), None
        )

        new_view = CardView(
            card_id=new_card.id,
            selected_rows={},
            focused_row_index=new_focused_row_index,
        )

        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card_with_view: CardWithView) -> list[Action]:
        if not card_with_view.card.kind == "TextCard":
            return []
        actions: list[Action] = []
        for row in card_with_view.get_marked_rows():
            previous_text = row.text
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
