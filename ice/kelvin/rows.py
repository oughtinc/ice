from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ice.kelvin.utils import generate_id

# from ice.kelvin.actions.base import Action
# -- circular import


RowId = str


class Row(BaseModel):
    id: RowId = Field(default_factory=generate_id)
    kind: str


class TextRow(Row):
    kind: Literal["Text"] = "Text"
    text: str


class PaperRow(Row):
    kind: Literal["Paper"] = "Paper"
    title: str | None
    authors: list[str]
    year: int | None
    citations: int | None
    raw_data: dict


# class ActionRow(Row):
#     kind: Literal["Action"] = "Action"
#     action: Action


ROW_TYPE_UNION = TextRow | PaperRow  # ActionRow
ROW_CLASSES = [TextRow, PaperRow]  # ActionRow
