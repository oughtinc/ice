import json
from typing import Iterable, Sequence
from ice.cache import diskcache
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard

from ice.paper import Paper, Paragraph, split_sentences

# @dataclass
# class PaperQaGoldStandard(Generic[AnswerType_contra]):
#     paper: Paper
#     question: str
#     gold_answer: AnswerType_contra
#     gold_support: Sequence[str]

TRAIN_PATH = "/code/datasets/qasper-train-v0.3.json"

VAL_PATH = "/code/datasets/qasper-dev-v0.3.json"

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
                sentences=split_sentences(paragraph),
            )
        )
    return paper

def _get_questions(question_dict: dict) -> list[dict]:
    question = question_dict["question"]

    answer = question_dict["answers"][0]["answer"] # We'll only use the first answer 

    if answer["unanswerable"] == True:
        return None
    
    keys = ["extractive_spans", "yes_no", "free_form_answer"]

    for key in keys:
        if answer[key]:
            return {"question": question, "answer": answer[key], "type": key, "support": answer["evidence"]}
    

def get_gold_standard(split: str, max_papers: int = 5) -> Iterable[PaperQaGoldStandard]:
    papers = get_papers(split)
    for i, (id, paper_dict) in enumerate(papers.items()):
        paper = _create_paper(paper_dict, id)
        for question_dict in paper_dict["qas"]:
            question = _get_questions(question_dict)
            if question:
                yield PaperQaGoldStandard(
                    paper=paper,
                    question=question["question"],
                    gold_answer=question["answer"],
                    gold_support=question["support"],
                )
        if i >= max_papers - 1:
            break

def qasper_support_func(
    document_id: str, GS: list[PaperQaGoldStandard]
) -> Sequence[PaperQaGoldStandard]:
    return [gs for gs in GS if gs.paper.document_id != document_id]
