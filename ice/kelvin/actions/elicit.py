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
from ice.kelvin.rows import PaperSectionRow
from ice.kelvin.rows import TextRow
from ice.kelvin.utils import truncate_text
from ice.recipes.elicit.search import elicit_search
from ice.recipes.elicit.vespa_search import vespa_search

log = get_logger()


class VespaSearchAction(Action):
    kind: Literal["VespaSearchAction"] = "VespaSearchAction"
    params: list[ActionParam] = [
        ActionParam(name="query", kind="TextParam", label="Query")
    ]
    label: str = "Search Vespa papers"

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
                    has_full_text=False,
                    sections=None,
                    raw_data=fields,
                )
            )
        old_card = frontier.focus_path_head()
        new_card = Card(rows=rows, prev_id=old_card.id, created_by_action=self)
        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card, new_view=View()
        )
        return new_frontier

    @classmethod
    def _instantiate_from_query(cls, query: str) -> Action:
        short_query = truncate_text(query, max_length=20)
        action = cls(
            label=f'Search papers for "{short_query}" (Vespa)',
            params=[
                ActionParam(name="query", kind="TextParam", label="Query", value=query)
            ],
        )
        return action

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        marked_rows = frontier.get_marked_rows()
        base_actions = [cls(label="Search papers (Vespa)")]
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

    kind: Literal["ViewPaper"] = "ViewPaper"
    params: list[ActionParam] = [
        ActionParam(name="paperRowId", kind="IdParam", label="Paper")
    ]
    label: str = "View paper"

    def execute(self, frontier: Frontier) -> PartialFrontier:

        card = frontier.focus_path_head()

        # Get the paper
        paper_id = self.params[0].value
        paper_row = next((row for row in card.rows if row.id == paper_id), None)
        if not paper_row:
            raise ValueError(f"Execute couldn't find paper for id {paper_id}")

        # Get paper info
        paper_row.is_expanded = True

        def make_section_row(section):
            log.info("Section", section=section)
            name = section.get("name")
            paragraphs = section.get("paragraphs", [])
            if hasattr(name, "get"):
                number = name.get("number")
                if not number:
                    number = ""
                else:
                    number = f"{number} "
                stringified_name = f"{number}{name.get('title')}"
            else:
                stringified_name = name
            return PaperSectionRow(
                paper=paper_row,
                title=stringified_name,
                preview=truncate_text(" ".join(paragraphs), max_length=100),
                paragraphs=paragraphs,
            )

        abstract = paper_row.raw_data["unsegmentedAbstract"]
        sections = paper_row.sections or []
        section_rows = [
            PaperSectionRow(
                paper=paper_row,
                title="Abstract",
                paragraphs=[abstract],
                preview=truncate_text(abstract, max_length=100),
                is_expanded=True,
            )
        ] + [make_section_row(section) for section in sections]

        # Convert to card & view
        new_rows = [paper_row] + section_rows
        new_card = Card(rows=new_rows, prev_id=card.id, created_by_action=self)
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


class ElicitSearchAction(Action):

    kind: Literal["FindPapers"] = "FindPapers"
    params: list[ActionParam] = [
        ActionParam(name="query", kind="TextParam", label="Query")
    ]
    label: str = "Search papers (Elicit)"

    def validate_input(self, card: Card) -> None:
        pass

    def execute(self, frontier) -> PartialFrontier:
        query = self.params[0].value
        search_result = asyncio.run(
            elicit_search(question=query, num_papers=7, filters={"has_pdf": True})
        )

        log.info("Search result", result=search_result)

        rows = []
        for (paper_id, paper_fields) in search_result.get("papers", {}).items():
            title = paper_fields.get("title", None)
            authors = paper_fields.get("authors", [])
            year = paper_fields.get("year", None)
            citations = paper_fields.get("citationCount", None)
            paragraphs = paper_fields.get("body", {}).get("value", {}).get("paragraphs")

            sections: list[dict] = []
            for paragraph in paragraphs:
                paragraph_sections = paragraph["sections"]
                section_name = (
                    paragraph_sections[0] if paragraph_sections else "(Unnamed section)"
                )
                found = False
                for section in sections:
                    if section["name"] == section_name:
                        section["paragraphs"].append(" ".join(paragraph["sentences"]))
                        found = True
                        break
                if not found:
                    sections.append(
                        {
                            "name": section_name,
                            "paragraphs": [" ".join(paragraph["sentences"])],
                        }
                    )

            rows.append(
                PaperRow(
                    title=title,
                    authors=authors,
                    year=year,
                    citations=citations,
                    has_full_text=(paragraphs != []),
                    sections=sections,
                    raw_data=paper_fields,
                )
            )
        old_card = frontier.focus_path_head()
        new_card = Card(rows=rows, prev_id=old_card.id, created_by_action=self)
        new_frontier = frontier.update_focus_path_head(
            new_head_card=new_card, new_view=View()
        )
        return new_frontier

    @classmethod
    def _instantiate_from_query(cls, query: str) -> Action:
        short_query = truncate_text(query, max_length=20)
        action = cls(
            label=f'Search papers for "{short_query}" (Elicit)',
            params=[
                ActionParam(name="query", kind="TextParam", label="Query", value=query)
            ],
        )
        return action

    @classmethod
    def instantiate(cls, frontier: Frontier) -> list[Action]:
        base_actions = [cls(label="Search papers")]
        # marked_rows = frontier.get_marked_rows()
        # if not marked_rows:
        #     return base_actions
        # elif len(marked_rows) == 1:
        #     marked_row = marked_rows[0]
        #     if isinstance(marked_row, TextRow):
        #         return base_actions + [cls._instantiate_from_query(marked_row.text)]
        #     elif isinstance(marked_row, PaperRow):
        #         if marked_row.title:
        #             return base_actions + [
        #                 cls._instantiate_from_query(marked_row.title) ]
        return base_actions
