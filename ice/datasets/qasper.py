import json
from typing import Iterable, Sequence
from ice.cache import diskcache
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard

from ice.paper import Paper, Paragraph, split_sentences
from pydantic import BaseModel

# @dataclass
# class PaperQaGoldStandard(Generic[AnswerType_contra]):
#     paper: Paper
#     question: str
#     gold_answer: AnswerType_contra
#     gold_support: Sequence[str]

TRAIN_PATH = "/code/datasets/qasper-train-v0.3.json"

VAL_PATH = "/code/datasets/qasper-dev-v0.3.json"

class RawAnswer(BaseModel):
    unanswerable: bool
    extractive_spans: list[str]
    yes_no: bool | None
    free_form_answer: str
    evidence: list[str]

@diskcache()
def get_papers(split: str) -> list[str]:
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
    paragraphs = sum([s["paragraphs"] for s in paper_dict["full_text"]], [])
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

def _replace_references(paragraph: str) -> str:
    for i in range(20):
        ref = f"BIBREF{i}"
        paragraph = paragraph.replace(ref, f"[{i+1}]")
    return paragraph

format_yes_no = lambda a: {True: "yes", False: "no", None: None}[a.yes_no]

format_extractive_spans = lambda a: " ".join(a.extractive_spans) if a.extractive_spans else None

format_free_form_answer = lambda a: a.free_form_answer if a.free_form_answer else None

formatters = [format_extractive_spans, format_free_form_answer, format_yes_no]

def _get_questions(question_dict: dict) -> tuple[str, list[str]]:
    question = question_dict["question"]

    answer_dict = question_dict["answers"][0]["answer"] # We'll only use the first answer 

    answer = RawAnswer.parse_obj(answer_dict)

    if answer.unanswerable:
        return "Not mentioned", []

    all_answers = list(filter(None, [f(answer) for f in formatters]))

    assert len(all_answers) == 1, "More than one answer type"

    return all_answers[0], answer.evidence


def get_gold_standard(split: str, max_papers: int = 5, max_questions_per_paper: int = 1) -> Iterable[PaperQaGoldStandard]:
    papers = get_papers(split)
    for i, (id, paper_dict) in enumerate(papers.items()):
        paper = _create_paper(paper_dict, id)
        for question_dict in paper_dict["qas"][:max_questions_per_paper]:
            answer_str, evidence = _get_questions(question_dict)
            if answer_str is None:
                continue
            question = question_dict["question"]
            if not "TABREF" in "".join(evidence) and not "FIGREF" in "".join(evidence):
                yield PaperQaGoldStandard(
                    paper=paper,
                    question=question,
                    gold_answer=answer_str,
                    gold_support=evidence,
                )
        if i >= max_papers - 1:
            break

def qasper_support_func(
    document_id: str, GS: list[PaperQaGoldStandard]
) -> Sequence[PaperQaGoldStandard]:
    return [gs for gs in GS if gs.paper.document_id != document_id]
