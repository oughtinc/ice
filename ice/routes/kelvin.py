import random
import string

from typing import Any
from typing import cast
from typing import Generic
from typing import List
from typing import Literal
from typing import TypeVar

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel, Field
from structlog import get_logger

log = get_logger()

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


def generate_id():
    """
    Generate a random card id of 8 alphanumeric characters
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


T = TypeVar("T")


class ActionParam(BaseModel):
    name: str
    kind: Literal["text_param", "int_param", "id_param"]
    value: Any
    label: str


class ActionParamInt(ActionParam):
    name: str
    kind: Literal["int_param"]
    value: int | None = None
    label: str = "Number"


class ActionParamId(ActionParam):
    name: str
    kind: Literal["id_param"]
    value: str | None = None
    label: str = "Id"


class ActionParamText(ActionParam):
    name: str
    kind: Literal["text_param"]
    value: str | None = None
    label: str = "Text"


class Action(BaseModel):
    kind: Literal["add_text_row_action", "edit_text_row_action"]
    params: List[ActionParam]
    id: str = Field(default_factory=generate_id)
    label: str


class Card(Generic[T], BaseModel):
    id: str
    kind: str
    rows: List[T]


class TextRow(BaseModel):
    text: str
    id: str = Field(default_factory=generate_id)


class TextCard(Card[TextRow]):
    kind: Literal["text_card"] = "text_card"
    rows: List[TextRow]


class ActionCard(Card[Action]):
    kind: Literal["action_card"] = "action_card"
    rows: list[Action]


class AddTextRowAction(Action):
    kind: Literal["add_text_row_action"] = "add_text_row_action"
    params: list[ActionParam] = [
        ActionParam(name="row_text", kind="text_param", label="Text")
    ]
    label: str = "Add bullet"


class EditTextRowAction(Action):
    kind: Literal["edit_text_row_action"] = "edit_text_row_action"
    params: list[ActionParam] = Field(
        default_factory=lambda: [
            ActionParam(name="new_row_text", kind="text_param", label="New text"),
            ActionParam(name="row_id", kind="id_param", label="Text Id"),
        ]
    )
    label: str = "Edit text"


def make_edit_text_row_action(card: Card, row_id: str) -> EditTextRowAction:
    rows = card.rows
    row = next((row for i, row in enumerate(rows) if row["id"] == row_id), None)
    if row is None:
        raise HTTPException(status_code=400, detail=f"Row id {row_id} not found")
    previous_text = row["text"]
    # truncate the previous text and add ellipsis if longer than 20 characters
    truncated_text = previous_text[:20] + ("..." if len(previous_text) > 20 else "")
    return EditTextRowAction(
        params=[
            ActionParam(name="new_row_text", kind="text_param", label="New text"),
            ActionParam(name="row_id", kind="id_param", value=row_id, label="Text Id"),
        ],
        label=f'Edit text "{truncated_text}"',
    )


class CardView(BaseModel):
    card_id: str
    selected_rows: dict[str, bool]
    available_actions: list[Action]


class CardWithView(BaseModel):
    card: Card
    view: CardView


class Workspace(BaseModel):
    cards: list[Card]
    view: CardView


@router.get("/hello/", response_model=str)
async def hello_world():
    return "Hello World"


@router.get("/workspaces/initial", response_model=Workspace)
async def initial_workspace():
    initial_card_id = generate_id()
    return Workspace(
        cards=[
            TextCard(
                id=initial_card_id,
                rows=[TextRow(text="one"), TextRow(text="two"), TextRow(text="three")],
            )
        ],
        view=CardView(
            card_id=initial_card_id,
            selected_rows={},
            available_actions=[AddTextRowAction()],
        ),
    )


def get_available_actions(card: Card, selected_rows: dict[str, bool]) -> list[Action]:
    # Return a list of actions that can be performed on the card
    # based on its kind and the selected row index

    if card.kind == "text_card":
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


def handle_add_action(action: AddTextRowAction, card: Card) -> CardWithView:

    if not action.kind == "add_text_row_action":
        raise HTTPException(
            status_code=400, detail=f"Unsupported action kind: {action.kind}"
        )

    if not card.kind == "text_card":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported card kind for add_text_row_action: {card.kind}",
        )

    # Get the new_row_text from the action params
    new_row_text = action.params[0].value
    # Generate a new card id
    new_card_id = generate_id()
    # Create a new text card with the new_row_text
    new_row = TextRow(text=new_row_text)
    new_card = TextCard(id=new_card_id, rows=card.rows + [new_row])
    # Create a new view for the new card
    new_view = CardView(
        card_id=new_card_id,
        selected_rows={},
        available_actions=get_available_actions(new_card, {}),
    )

    # Return the new card and view
    return CardWithView(card=new_card, view=new_view)


def handle_edit_action(action: EditTextRowAction, card: Card) -> CardWithView:

    log.info("handle_edit_action", action=action, card=card)

    # Validate the action and card kinds
    if not action.kind == "edit_text_row_action":
        raise HTTPException(
            status_code=400, detail=f"Unsupported action kind: {action.kind}"
        )

    if not card.kind == "text_card":
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported card kind for edit_text_row_action: {card.kind}",
        )

    # Get the new_row_text and row_id from the action params
    # FIXME: Don't access by position
    new_row_text = action.params[0].value
    row_id = action.params[1].value

    # Create a map from row ids to row texts
    row_id_map = {row["id"]: row["text"] for row in card.rows}

    # Validate the row_id
    if row_id not in row_id_map:
        raise HTTPException(status_code=400, detail=f"Invalid row id: {row_id}")

    # Create a new list of rows by updating the row text if the row id matches the action row_id
    new_rows = [
        TextRow(id=row["id"], text=new_row_text if row["id"] == row_id else row["text"])
        for row in card.rows
    ]

    # Create a new text card with the updated rows
    new_card = TextCard(id=generate_id(), rows=new_rows)

    # Create a new view for the new card
    new_view = CardView(
        card_id=new_card.id,
        # Filter the row ids that have a true value in the selected_rows map
        selected_rows={},
        # Update the available_actions to use row_id instead of row_index
        available_actions=get_available_actions(new_card, {}),
    )

    log.info("handle_edit_action", new_card=new_card, new_view=new_view)

    # Return the new card and view
    return CardWithView(card=new_card, view=new_view)


@router.post("/actions/execute", response_model=CardWithView)
async def execute_action(action: Action, card: Card):

    # Dispatch based on the action kind
    if action.kind == "add_text_row_action":
        return handle_add_action(cast(AddTextRowAction, action), card)
    elif action.kind == "edit_text_row_action":
        return handle_edit_action(cast(EditTextRowAction, action), card)
    else:
        raise HTTPException(
            status_code=400, detail=f"Unsupported action kind: {action.kind}"
        )


@router.post("/actions/available", response_model=list[Action])
async def available_actions(card: Card, view: CardView):
    return get_available_actions(card, view.selected_rows)
