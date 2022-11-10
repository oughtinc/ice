from collections.abc import Sequence
from itertools import chain

from ice.metrics.gold_standards import load_papers
from ice.paper import Paper
from ice.recipes.consort_flow.generate_questions import arms_questions_and_answers
from ice.recipes.consort_flow.generate_questions import (
    experiments_questions_and_answers,
)
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.meta.eval_paper_qa.common_baselines import (
    cheating_few_shot_qa_baseline,
)
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard


def experiments_few_shot_demonstration(
    document_id: str, consolidate: bool = False
) -> Sequence[PaperQaGoldStandard]:
    papers = [
        p
        for p in load_papers(split="validation", question_short_name="experiments_arms")
        if p.document_id != document_id
    ]
    gss = [get_ea_gs(p.document_id) for p in papers]
    paper_gs = list(
        chain(
            *[
                experiments_questions_and_answers(gs, consolidate=consolidate)
                for gs in gss
                if gs
            ]
        )
    )
    return paper_gs


def arms_few_shot_demonstration(
    document_id: str, consolidate: bool = False
) -> Sequence[PaperQaGoldStandard]:
    papers = [
        p
        for p in load_papers(split="validation", question_short_name="experiments_arms")
        if p.document_id != document_id
    ]
    gss = [get_ea_gs(p.document_id) for p in papers]
    paper_gs = list(
        [arms_questions_and_answers(gs, consolidate=consolidate) for gs in gss if gs]
    )
    used_gs = []
    for paper in paper_gs:
        for gs in paper:
            # 1 per paper
            used_gs.append(gs)
            break

    return used_gs


def _to_paragraphs(paper: Paper) -> Sequence[str]:
    return [str(p) for p in paper.nonempty_paragraphs()]


def _to_sentences(paper: Paper) -> Sequence[str]:
    return [s for s in paper.sentences() if s]


async def cheating_few_shot_qa_experiments_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await cheating_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=experiments_few_shot_demonstration,
    )


async def cheating_few_shot_qa_experiments_paragraph_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await cheating_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=experiments_few_shot_demonstration,
        paper_division_func=_to_paragraphs,
    )


async def cheating_few_shot_qa_experiments_paragraph_reasoning_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await cheating_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=experiments_few_shot_demonstration,
        paper_division_func=_to_paragraphs,
        reasoning=True,
    )
