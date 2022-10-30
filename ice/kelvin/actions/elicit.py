import asyncio

from typing import Literal

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.cards.base import Card
from ice.kelvin.cards.paper import PaperCard
from ice.kelvin.cards.paper import PaperRow
from ice.kelvin.cards.text import TextCard
from ice.kelvin.cards.text import TextRow
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
                    raw_data=paper_fields,
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


class ViewPaperAction(Action):

    kind: Literal["ViewPaperAction"] = "ViewPaperAction"
    params: list[ActionParam] = [
        ActionParam(name="paperRowId", kind="IdParam", label="Paper")
    ]
    label: str = "View paper"

    def validate_input(self, card: Card) -> None:
        if not card.kind == "PaperCard":
            raise ValueError("ViewPaperAction can only be applied to paper cards")

    def execute(self, card: Card) -> CardWithView:
        new_row_text = self.params[0].value
        new_row = TextRow(text=new_row_text)
        new_rows = card.rows + [new_row]

        # Get the paper
        paper_id = self.params[0].value
        paper = next((row for row in card.rows if row.id == paper_id), None)
        if not paper:
            raise ValueError(f"Execute couldn't find paper for id {paper_id}")

        # Get each paragraph from the paper
        abstract = paper.raw_data["abstract"]
        body = paper.raw_data["body"]["value"]
        text_bullets = []
        MAX_BULLET_LEN = 200  # chars
        for paragraph in abstract["paragraphs"] + body["paragraphs"]:
            bullet = ""
            for sentence in paragraph["sentences"]:
                bullet += f"{sentence} "
                if len(bullet) >= MAX_BULLET_LEN:
                    text_bullets.append(bullet)
                    bullet = ""
            if bullet:
                text_bullets.append(bullet)
                bullet = ""

        # Convert to card & view
        new_rows = [TextRow(text=text) for text in text_bullets]
        new_card = TextCard(rows=new_rows)
        new_view = CardView(
            card_id=new_card.id,
            selected_rows={},
        )

        return CardWithView(card=new_card, view=new_view)

    @classmethod
    def instantiate(cls, card: Card, selected_rows: dict[str, bool]) -> list[Action]:
        actions: list[Action] = []
        if card.kind == "PaperCard":
            for row in card.get_selected_rows(selector=selected_rows):
                paper_id = row.id
                title = row.title
                short_title = truncate_text(title, max_length=80)
                action = cls(
                    label=f'View paper "{short_title}"',
                    params=[
                        ActionParam(
                            name="paperRowId",
                            kind="IdParam",
                            label="Paper",
                            value=paper_id,
                        )
                    ],
                )
                actions.append(action)
        return actions
