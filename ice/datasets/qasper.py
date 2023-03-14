import json
import re
from collections.abc import Sequence
from itertools import islice
from typing import Optional

from pydantic import BaseModel
from pydantic import validator

from ice.cache import diskcache
from ice.paper import Paper
from ice.paper import Paragraph
from ice.paper import split_sentences
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard


TRAIN_PATH = "/code/datasets/qasper-train-v0.3.json"

VAL_PATH = "/code/datasets/qasper-dev-v0.3.json"


class RawAnswer(BaseModel):
    unanswerable: bool
    extractive_spans: list[str]
    yes_no: Optional[bool]
    free_form_answer: str
    evidence: list[str]

    @validator("evidence")
    def transform_evidence(cls, v: list[str]) -> list[str]:
        return [_replace_references(para) for para in v]

    # TODO: Skip where any evidence starts with FLOAT_SELECTED

    def canonical_answer(self) -> Optional[str]:
        if self.unanswerable:
            return "Not mentioned"
        answers = tuple(
            filter(None, (self.yes_no, self.free_form_answer, self.extractive_spans))
        )
        assert len(answers) == 1, "Expected exactly one answer type"
        answer = answers[0]
        if isinstance(answer, bool):
            return "yes" if answer else "no"
        elif isinstance(answer, str):
            return answer
        elif isinstance(answer, list):
            return "...".join(answer)
        else:
            raise TypeError(f"Unexpected answer type: {type(answer)}")


@diskcache()
def load_qasper_json(split: str) -> dict[str, dict]:
    path = TRAIN_PATH if split == "train" else VAL_PATH
    with open(path) as f:
        return json.load(f)


def _create_paper(paper_dict: dict, key: str) -> Paper:
    paper = Paper(
        document_id=key,
        paragraphs=[
            Paragraph(
                sectionType="abstract",
                sections=[],
                sentences=split_sentences(paper_dict["abstract"]),
            )
        ],
    )
    paragraphs: list[str] = sum([s["paragraphs"] for s in paper_dict["full_text"]], [])
    paragraphs = [p for p in paragraphs if p]
    for paragraph in paragraphs:
        paper.paragraphs.append(
            Paragraph(
                sectionType="main",
                sections=[],
                sentences=split_sentences(_replace_references(paragraph)),
            )
        )
    return paper


BIBREF_PATTERN = re.compile(r"BIBREF(\d+)")
TABFIGREF_PATTERN = re.compile(r"(TABREF|FIGREF)(\d+)")


def _match_to_subsequent_int_value(match: re.Match) -> str:
    return f"{int(match.groups()[-1]) + 1}"


def _replace_references(paragraph: str) -> str:
    unbibref = re.sub(
        BIBREF_PATTERN, lambda m: f"[{_match_to_subsequent_int_value(m)}]", paragraph
    )
    return re.sub(TABFIGREF_PATTERN, _match_to_subsequent_int_value, unbibref)


def _get_answers(question_dict: dict) -> tuple[Optional[str], list[str]]:
    answer_dict = question_dict["answers"][0][
        "answer"
    ]  # We'll only use the first answer

    answer = RawAnswer.parse_obj(answer_dict)

    return answer.canonical_answer(), answer.evidence


# class QasperSection(BaseModel):
#     section_name: str
#     paragraphs: Sequence[str]


# class QasperAnswer(BaseModel):
#     answer: RawAnswer


# class QasperQas(BaseModel):
#     question: str
#     question_id: str
#     answers: Sequence[QasperAnswer]


# class QasperPaperInfo(BaseModel):
#     title: str
#     abstract: str
#     full_text: Sequence[QasperSection]
#     qas: Sequence[QasperQas]


def generate_qasper_qas(split: str):
    qasper_info = load_qasper_json(split)
    for i, (id, paper_dict) in enumerate(qasper_info.items()):
        paper = _create_paper(paper_dict, id)
        for question_dict in paper_dict["qas"]:
            answer_str, evidence = _get_answers(question_dict)
            if answer_str is None:
                continue
            question = question_dict["question"]
            yield PaperQaGoldStandard(
                paper=paper,
                question=question,
                short_gold_answer=answer_str,
                gold_answer=answer_str,
                gold_support=evidence,
            )


def limited_generate_qasper_qas(split: str):
    LIMIT = 10
    yield from islice(generate_qasper_qas(split), LIMIT)


def qasper_support_func(
    document_id: str, GS: list[PaperQaGoldStandard]
) -> Sequence[PaperQaGoldStandard]:
    return [gs for gs in GS if gs.paper.document_id != document_id]
