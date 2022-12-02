from typing import Literal

from pydantic import BaseModel
from pydantic import Field

from ice.kelvin.utils import generate_id

# from ice.kelvin.actions.base import Action
# -- circular import


RowId = str


class Row(BaseModel):
    id: RowId = Field(default_factory=generate_id)
    kind: str

    def __str__(self):
        return f"""<row id="{self.id}" kind="{self.kind}"/>"""

    def readable_value(self):
        return None


class TextRow(Row):
    kind: Literal["Text"] = "Text"
    text: str

    def __str__(self):
        return f"""<row id="{self.id}" kind="text">{self.text}</row>"""

    def readable_value(self):
        return self.text


class PaperRow(Row):
    kind: Literal["Paper"] = "Paper"
    title: str | None
    authors: list[str]
    year: int | None
    citations: int | None
    has_full_text: bool
    sections: list[dict] | None
    raw_data: dict
    is_expanded: bool = False

    def __str__(self):
        if self.is_expanded:
            return f"""<row id="{self.id}" kind="paper" title="{self.title}" year="{self.year}" citations="{self.citations}" doi="{self.raw_data.get('doi')}" has_full_text="{self.has_full_text}" is_expanded="true"/>"""
        else:
            return f"""<row id="{self.id}" kind="paper" title="{self.title}" authors="{self.authors}" year="{self.year}" has_full_text="{self.has_full_text}" is_expanded="false"/>"""

    def readable_value(self):
        return self.title


class PaperSectionRow(Row):
    kind: Literal["PaperSection"] = "PaperSection"
    paper: PaperRow
    title: str
    paragraphs: list[str]
    is_expanded: bool = False
    preview: str

    def __str__(self):
        if self.is_expanded:
            section_text = "\n\n".join(self.paragraphs)
            return f"""<row id="{self.id}" kind="paper_section" title="{self.title}" paper="{self.paper.id}" is_expanded="true">{section_text}</row>"""
        else:
            return f"""<row id="{self.id}" kind="paper_section" title="{self.title}" paper="{self.paper.id}" is_expanded="false">{self.preview}</row>"""

    def readable_value(self):
        return self.title

    def as_markdown(self):
        paragraphs_text = "\n\n".join(self.paragraphs)
        return f"""# {self.title}

{paragraphs_text}"""


# class ActionRow(Row):
#     kind: Literal["Action"] = "Action"
#     action: Action


ROW_TYPE_UNION = TextRow | PaperRow | PaperSectionRow  # ActionRow
ROW_CLASSES = [TextRow, PaperRow, PaperSectionRow]  # ActionRow
