from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.actions.text import AddTextRowAction
from ice.kelvin.actions.text import EditTextRowAction
from ice.kelvin.cards.base import Card

ACTION_TYPE_UNION = AddTextRowAction | EditTextRowAction


def make_edit_text_row_action(card: Card, row_id: str) -> EditTextRowAction:
    # TODO: This should be a class method on EditTextRowAction?
    rows = card.rows
    row = next((row for i, row in enumerate(rows) if row["id"] == row_id), None)
    if row is None:
        raise ValueError(f"Row id {row_id} not found")
    previous_text = row["text"]
    # truncate the previous text and add ellipsis if longer than 20 characters
    truncated_text = previous_text[:20] + ("..." if len(previous_text) > 20 else "")
    return EditTextRowAction(
        params=[
            ActionParam(name="new_row_text", kind="TextParam", label="New text"),
            ActionParam(name="row_id", kind="IdParam", value=row_id, label="Text Id"),
        ],
        label=f'Edit text "{truncated_text}"',
    )


def get_available_actions(card: Card, selected_rows: dict[str, bool]) -> list[Action]:
    # Return a list of actions that can be performed on the card
    # based on its kind and the selected row index

    if card.kind == "TextCard":
        # For text cards, the available actions are adding a new row
        # or editing an existing row
        actions: list[Action] = [AddTextRowAction()]
        if selected_rows:
            for (selected_row_id, is_selected) in selected_rows.items():
                if not is_selected:
                    continue
                actions.append(
                    make_edit_text_row_action(card=card, row_id=selected_row_id)
                )
        return actions
    else:
        raise NotImplementedError(f"Unsupported card kind: {card.kind}")
