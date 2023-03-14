import re
from collections.abc import Iterator
from functools import cache
from pathlib import Path
from typing import Annotated
from typing import Literal
from typing import Optional

import nltk
import requests
from nltk.tokenize import sent_tokenize
from pydantic import BaseModel
from pydantic import Field
from structlog.stdlib import get_logger

from ice.cache import diskcache
from ice.environment import env
from ice.settings import OUGHT_ICE_DIR

log = get_logger()

PDF_PARSER_URL = "https://test.elicit.org/elicit-previews/james/oug-3083-support-parsing-arbitrary-pdfs-using/parse_pdf"

SectionType = Literal["abstract", "main", "back"]


@cache
def download_punkt():
    try:
        sent_tokenize("")
    except LookupError:
        nltk.download("punkt", quiet=False)


def get_full_document_id(document_id: str) -> str:
    return {
        "abebe-2018-tiny.txt": "abebe-2018.pdf",
        "keenan-2018-tiny.txt": "keenan-2018.pdf",
    }.get(document_id, document_id)


def get_paper_paths(paper_dir: Optional[Path] = None) -> list[Path]:
    if paper_dir is None:
        script_path = Path(__file__).parent.parent
        paper_dir = script_path / "papers/"
    paper_paths = [f for f in paper_dir.iterdir() if f.suffix in (".pdf", ".txt")]
    paper_paths = sorted(paper_paths)
    return paper_paths


def starts_with_number(s: str) -> bool:
    return re.match(r"^\d+", s) is not None


def is_likely_section_title(text: str):
    return (starts_with_number(text) and len(text) < 200) or text == "Abstract"


def split_sentences(text: str) -> list[str]:
    download_punkt()
    return sent_tokenize(text)


def section_title_words(title: str) -> str:
    if not starts_with_number(title):
        return title
    return " ".join(title.split(" ")[1:])


def section_title_number(title: str) -> str:
    if not starts_with_number(title):
        return ""
    return title.split(" ")[0]


def parse_txt(file: Path) -> list[dict]:
    body = []
    with open(file) as text_file:
        text = text_file.read()
        paragraphs = text.split("\n\n")
        current_section = "Introduction"
        for paragraph in paragraphs:
            if is_likely_section_title(paragraph):
                current_section = paragraph
            else:
                sentences = split_sentences(paragraph)
                body.append(
                    {
                        "sentences": sentences,
                        "sections": [
                            {
                                "title": section_title_words(current_section),
                                "number": section_title_number(current_section),
                            }
                        ],
                        "sectionType": "abstract"
                        if current_section == "Abstract"
                        else "main",
                    }
                )
    return body


def save_pdf_text(paper_body: list[dict], file_name: str):
    """
    Save pdf text to help with debugging.
    """
    paper_txt_dir = OUGHT_ICE_DIR / "paper_txt"
    paper_txt_dir.mkdir(parents=True, exist_ok=True)
    open(paper_txt_dir / f"{file_name}.txt", "w").write(
        "\n\n".join(" ".join(paragraph["sentences"]) for paragraph in paper_body)
    )


@diskcache()
def parse_pdf(file: Path) -> list[dict]:
    with env().spinner(f"[bold green] Parsing {file.name}"):
        files = {"pdf": open(file, "rb")}
        r = requests.post(PDF_PARSER_URL, files=files)
        body = r.json()
        save_pdf_text(body, file.name)
    env().print(f"Parsed {file.name}.")
    return body


class Section(BaseModel):
    title: str
    number: Optional[str] = None


class Paragraph(BaseModel):
    sentences: list[str]
    sections: list[Section]
    section_type: Annotated[SectionType, Field(alias="sectionType")]

    def is_body_paragraph(self):
        return self.section_type in ("abstract", "main")

    def is_empty(self):
        return str(self).strip() == ""

    def __str__(self):
        return " ".join(self.sentences)

    def __hash__(self):
        return hash(str(self))


class Paper(BaseModel):
    paragraphs: list[Paragraph]
    document_id: str = "unknown"

    @classmethod
    def load(cls, file: Path) -> "Paper":
        document_id = file.name

        if file.suffix == ".pdf":
            paragraph_dicts = parse_pdf(file)
        elif file.suffix == ".txt":
            paragraph_dicts = parse_txt(file)
        else:
            raise ValueError(f"Unknown extension: {file.suffix}")

        if len(paragraph_dicts) < 3:
            log.warn(f"paper {document_id} only has {len(paragraph_dicts)} paragraphs")

        return Paper.parse_obj(
            dict(paragraphs=paragraph_dicts, document_id=document_id)
        )

    def sentences(self) -> Iterator[str]:
        for paragraph in self.paragraphs:
            for sentence in paragraph.sentences:
                yield sentence

    def nonempty_paragraphs(self) -> list[Paragraph]:
        return [p for p in self.paragraphs if not p.is_empty()]

    def __str__(self):
        return "\n\n".join(str(p) for p in self.paragraphs)

    def dict(self, *args, **kwargs):
        kwargs["exclude"] = {"paragraphs"}
        return super().dict(*args, **kwargs)
