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
from pydantic import BaseModel
from structlog import get_logger

log = get_logger()

router = APIRouter(prefix="/kelvin", tags=["kelvin"])


def generate_card_id():
    """
    Generate a random card id of 8 alphanumeric characters
    """
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))


T = TypeVar("T")


class ActionParam(BaseModel):
    name: str
    kind: Literal["text_param", "int_param"]
    value: Any


class ActionParamInt(ActionParam):
    name: str
    kind: Literal["int_param"]
    value: int | None = None


class ActionParamText(ActionParam):
    name: str
    kind: Literal["text_param"]
    value: str | None = None


class Action(BaseModel):
    kind: Literal["add_text_row_action", "edit_text_row_action"]
    params: List[ActionParam]


class Card(Generic[T], BaseModel):
    id: str
    kind: str
    rows: List[T]


class TextCard(Card[str]):
    kind: Literal["text_card"] = "text_card"
    rows: List[str]


class ActionCard(Card[Action]):
    kind: Literal["action_card"] = "action_card"
    rows: list[Action]


class AddTextRowAction(Action):
    kind: Literal["add_text_row_action"] = "add_text_row_action"
    params: list[ActionParam] = [ActionParam(name="row_text", kind="text_param")]


class EditTextRowAction(Action):
    kind: Literal["edit_text_row_action"] = "edit_text_row_action"
    params: list[ActionParam] = [
        ActionParam(name="new_row_text", kind="text_param"),
        ActionParam(name="row_index", kind="int_param"),
    ]


class CardView(BaseModel):
    card_id: str
    selected_row_index: int | None = None
    available_actions: List[Action]


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
    initial_card_id = generate_card_id()
    return Workspace(
        cards=[TextCard(id=initial_card_id, rows=[])],
        view=CardView(
            card_id=initial_card_id,
            selected_row_index=None,
            available_actions=[AddTextRowAction()],
        ),
    )


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
    new_card_id = generate_card_id()
    # Create a new text card with the new_row_text
    new_card = TextCard(id=new_card_id, rows=card.rows + [new_row_text])
    # Create a new view for the new card
    new_view = CardView(
        card_id=new_card_id,
        selected_row_index=len(new_card.rows) - 1,
        available_actions=[
            AddTextRowAction(),
            EditTextRowAction(
                params=[
                    ActionParam(name="new_row_text", kind="text_param"),
                    ActionParam(
                        name="row_index", kind="int_param", value=len(new_card.rows) - 1
                    ),
                ]
            ),
        ],
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

    # Get the new_row_text and row_index from the action params
    # FIXME: Don't access by position
    new_row_text = action.params[0].value
    row_index = int(action.params[1].value)

    # Validate the row_index
    if not 0 <= row_index < len(card.rows):
        raise HTTPException(status_code=400, detail=f"Invalid row index: {row_index}")

    # Create a copy of the card rows and update the row at the given index
    new_rows = card.rows.copy()
    new_rows[row_index] = new_row_text

    # Create a new text card with the updated rows
    new_card = TextCard(id=generate_card_id(), rows=new_rows)

    # Create a new view for the new card
    new_view = CardView(
        card_id=new_card.id,
        selected_row_index=row_index,
        available_actions=[
            AddTextRowAction(),
            EditTextRowAction(
                params=[
                    ActionParam(name="new_row_text", kind="text_param"),
                    ActionParam(name="row_index", kind="int_param", value=row_index),
                ]
            ),
        ],
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
