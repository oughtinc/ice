from pydantic import BaseModel
from pydantic import Field

from ice.kelvin.utils import generate_id


class CardRow(BaseModel):
    id: str


class Card(BaseModel):
    id: str = Field(default_factory=generate_id)
    kind: str
    rows: list[CardRow]
