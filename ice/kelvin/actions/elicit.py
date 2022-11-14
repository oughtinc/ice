import asyncio

from typing import Literal

from structlog import get_logger

from ice.kelvin.actions.base import Action
from ice.kelvin.actions.base import ActionParam
from ice.kelvin.models import Card
from ice.kelvin.models import Frontier
from ice.kelvin.models import PartialFrontier
from ice.kelvin.models import View
from ice.kelvin.rows import PaperRow
from ice.kelvin.rows import TextRow
from ice.kelvin.utils import truncate_text
from ice.recipes.elicit.vespa_search import vespa_search

log = get_logger()


class VespaSearchAction(Action):
    kind: Literal["VespaSearchAction"] = "VespaSearchAction"
    params: list[ActionParam] = [
        ActionParam(name="query", kind="TextParam", label="Query")
    ]
    label: str = "Search papers"

    def execute(self, frontier) -> PartialFrontier:
        query = self.params[0].value
        search_result = asyncio.run(vespa_search(query=query, num_hits=20))

        log.info("Search result", result=search_result)

        rows = []
        for record in search_result.get("root", {}).get("children", []):
            fields = record.get("fields", {})
            title = fields.get("title", "")
            # abstract = fields.get("abstract", "")
            authors = [author.get("name") for author in fields.get("authors", [])]
            publication_year = fields.get("publicationYear", "")
            # doi = fields.get("doi", "")
            citations = fields.get("citedByCount", "")
            rows.append(
                PaperRow(
                    title=title,
                    authors=authors,
                    year=publication_year,
                    citations=citations,
                    raw_data=fields,
                )
            )
        old_card = frontier.focus_path_head()
        new_card = Card(rows=rows, prev_id=old_card.id)
        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card, new_view=View()
        )
        return new_frontier

    @classmethod
    def _instantiate_from_query(cls, query: str) -> Action:
        short_query = truncate_text(query, max_length=20)
        action = cls(
            label=f'Search papers for "{short_query}"',
            params=[
                ActionParam(name="query", kind="TextParam", label="Query", value=query)
            ],
        )
        return action

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        marked_rows = frontier.get_marked_rows()
        base_actions = [cls(label="Search papers")]
        if not marked_rows:
            return base_actions
        elif len(marked_rows) == 1:
            marked_row = marked_rows[0]
            if isinstance(marked_row, TextRow):
                return base_actions + [cls._instantiate_from_query(marked_row.text)]
            elif isinstance(marked_row, PaperRow):
                if marked_row.title:
                    return base_actions + [
                        cls._instantiate_from_query(marked_row.title)
                    ]
        return []


class ViewPaperAction(Action):

    kind: Literal["ViewPaperAction"] = "ViewPaperAction"
    params: list[ActionParam] = [
        ActionParam(name="paperRowId", kind="IdParam", label="Paper")
    ]
    label: str = "View paper"

    def execute(self, frontier: Frontier) -> PartialFrontier:

        card = frontier.focus_path_head()

        # Get the paper
        paper_id = self.params[0].value
        paper = next((row for row in card.rows if row.id == paper_id), None)
        if not paper:
            raise ValueError(f"Execute couldn't find paper for id {paper_id}")

        # Get paper info
        abstract = paper.raw_data["abstract"]
        text_bullets = [
            f"Title: {paper.title}",
            "Authors: " + ", ".join(paper.authors),
            f"Year: {paper.year}",
            f"Citations: {paper.citations}",
            f"DOI: {paper.raw_data.get('doi')}",
            f"Abstract: {abstract}",
        ]

        # Convert to card & view
        new_rows = [TextRow(text=text) for text in text_bullets]
        new_card = Card(rows=new_rows, prev_id=card.id)
        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card, new_view=View()
        )
        return new_frontier

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        actions: list[Action] = []
        for row in frontier.get_marked_rows():
            if row.kind == "Paper":
                paper_id = row.id
                title = row.title
                short_title = truncate_text(title or "(not title)", max_length=80)
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
