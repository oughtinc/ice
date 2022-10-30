from pydantic import BaseModel

from ice.kelvin.cards.all import CARD_TYPE_UNION


class CardView(BaseModel):
    card_id: str
    selected_rows: dict[str, bool]


class CardWithView(BaseModel):
    card: CARD_TYPE_UNION
    view: CardView
