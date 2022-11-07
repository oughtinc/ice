from pydantic import BaseModel

from ice.kelvin.cards.all import CARD_TYPE_UNION
from ice.kelvin.cards.base import CardRow


class CardView(BaseModel):
    card_id: str
    selected_rows: dict[str, bool]
    focused_row_index: int | None


class CardWithView(BaseModel):
    card: CARD_TYPE_UNION
    view: CardView

    def get_marked_rows(self) -> list[CardRow]:
        """
        Return a list of row dicts from the card that are selected
        """
        rows: list[CardRow] = self.card.rows
        return [
            row
            for (index, row) in enumerate(rows)
            if self.view.selected_rows.get(row.id, False)
            or index == self.view.focused_row_index
        ]
