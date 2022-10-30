from pydantic import BaseModel
from pydantic import Field

from ice.kelvin.utils import generate_id


class CardRow(BaseModel):
    id: str


class Card(BaseModel):
    id: str = Field(default_factory=generate_id)
    kind: str
    rows: list[CardRow]

    def get_selected_rows(self, selector: dict[str, bool]) -> list[CardRow]:
        """
        Return a list of row dicts from the card that are selected
        """
        rows = self.rows
        return [row for row in rows if selector.get(row.id, False)]
