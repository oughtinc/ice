from collections.abc import Callable
from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from structlog import get_logger

from ice.kelvin.models import Card
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.models import View
from ice.kelvin.rows import Row
from ice.kelvin.utils import generate_id

log = get_logger()


class ActionParam(BaseModel):
    name: str
    kind: Literal["TextParam", "IntParam", "IdParam"]
    value: Any
    label: str
    default_value: Any = None


class ActionParamInt(ActionParam):
    name: str
    kind: Literal["IntParam"] = "IntParam"
    value: int | None = None
    label: str = "Number"
    default_value: int | None = None


class ActionParamId(ActionParam):
    name: str
    kind: Literal["IdParam"] = "IdParam"
    value: str | None = None
    label: str = "Id"
    default_value: str | None = None


class ActionParamText(ActionParam):
    name: str
    kind: Literal["TextParam"] = "TextParam"
    value: str | None = None
    label: str = "Text"
    default_value: str | None = None


class Action(BaseModel):
    id: str = Field(default_factory=generate_id)
    kind: str
    params: list[ActionParam]
    label: str

    def validate_input(self, frontier: Frontier) -> None:
        pass

    def execute(self, frontier: Frontier) -> PartialFrontier:
        raise NotImplementedError

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list["Action"]:
        raise NotImplementedError

    def __str__(self):
        if len(self.params) == 0:
            return f"""<action kind="{self.kind}" />"""
        elif len(self.params) == 1:
            return f"""<action kind="{self.kind}">{self.params[0].value}</action>"""
        return f"""<action kind="{self.kind}">{self.params}</action>"""


def update_row_in_frontier(
    frontier: Frontier, row_id: str, update_fn: Callable[[Row], Row], action: Action
) -> PartialFrontier:
    card = frontier.focus_path_head()

    def _update_row(row):
        # Update row id to new id
        row = row.copy()
        row.id = generate_id()
        return update_fn(row)

    new_rows = [_update_row(row) if row.id == row_id else row for row in card.rows]

    new_card = Card(rows=new_rows, prev_id=card.id, created_by_action=action)

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
