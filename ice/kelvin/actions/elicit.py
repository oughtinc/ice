import asyncio

from typing import Literal

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.paper import PaperCard
from ice.kelvin.cards.paper import PaperRow
from ice.kelvin.utils import truncate_text
from ice.kelvin.view import CardView
from ice.kelvin.view import CardWithView
from ice.recipes.elicit.search import elicit_search


class ElicitSearchAction(Action):

    kind: Literal["ElicitSearchAction"] = "ElicitSearchAction"
    params: list[ActionParam] = [
        ActionParam(name="query", kind="TextParam", label="Query")
    ]
    label: str = "Search Elicit papers"

    def validate_input(self, card: Card) -> None:
        pass

    def execute(self, card: Card) -> CardWithView:
        query = self.params[0].value
        search_result = asyncio.run(elicit_search(question=query, num_papers=5))

        rows = []
        for (paper_id, paper_fields) in search_result.get("papers", {}).items():
            title = paper_fields.get("title", None)
            authors = paper_fields.get("authors", [])
            year = paper_fields.get("year", None)
            citations = paper_fields.get("citationCount", None)
            rows.append(
                PaperRow(
                    title=title,
                    authors=authors,
                    year=year,
                    citations=citations,
                    raw_data=search_result,
                )
            )

        new_card = PaperCard(rows=rows)
        new_view = CardView(card_id=new_card.id, selected_rows={})
        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card: Card, selected_rows: dict[str, bool]) -> list[Action]:
        actions: list[Action] = [cls(label="Search Elicit papers (enter query)")]
        if card.kind == "TextCard":
            for row in card.get_selected_rows(selector=selected_rows):
                query = row.text
                short_query = truncate_text(query, max_length=20)
                action = cls(
                    label=f'Search Elicit papers (query "{short_query}")',
                    params=[
                        ActionParam(
                            name="query", kind="TextParam", label="Query", value=query
                        )
                    ],
                )
                actions.append(action)
        return actions
