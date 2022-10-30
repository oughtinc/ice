from pydantic import BaseModel

from ice.kelvin.cards.base import Card


class CardView(BaseModel):
    card_id: str
    selected_rows: dict[str, bool]


class CardWithView(BaseModel):
    card: Card
    view: CardView
