from typing import Any
from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from structlog import get_logger

from ice.kelvin.cards.base import Card
from ice.kelvin.utils import generate_id
from ice.kelvin.view import CardWithView

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
    kind: str
    params: list[ActionParam]
    id: str = Field(default_factory=generate_id)
    label: str

    def validate_input(self, card: Card) -> None:
        raise NotImplementedError

    def execute(self, card: Card) -> CardWithView:
        raise NotImplementedError

    @classmethod
    def instantiate(cls, card_with_view: CardWithView) -> list["Action"]:
        raise NotImplementedError
