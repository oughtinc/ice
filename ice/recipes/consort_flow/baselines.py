from collections.abc import Sequence
from itertools import chain
from ice.apis.openai import TooLongRequestError

from ice.metrics.gold_standards import load_papers
from ice.paper import Paper
from ice.recipes.consort_flow.baseline_elicit_answer import answer_like_elicit_qa
from ice.recipes.consort_flow.generate_questions import arms_questions_and_answers
from ice.recipes.consort_flow.generate_questions import (
    experiments_questions_and_answers,
)
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.meta.eval_paper_qa.common_baselines import (
    cheating_few_shot_qa_baseline,
    cheating_qa_baseline_list_answer,
)
from ice.recipes.meta.eval_paper_qa.quick_list import quick_list
from ice.recipes.meta.eval_paper_qa.types import PaperQaAnswer, PaperQaGoldStandard
from ice.recipes.primer.qa import answer
from ice.recipes.program_search.nodes.decontext.decontextualize import paper_decontext
from ice.recipes.program_search.nodes.prune.prune import prune
from ice.recipes.program_search.nodes.select.select import (
    remove_lowest_perplexity,
    select_using_elicit_prompt_few_shot,
    windowed_select_using_elicit_prompt,
)


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


async def cheating_few_shot_qa_arms_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await cheating_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=arms_few_shot_demonstration,
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


async def cheating_few_shot_qa_arms_paragraph_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await cheating_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=arms_few_shot_demonstration,
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


async def cheating_few_shot_qa_arms_paragraph_reasoning_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await cheating_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=arms_few_shot_demonstration,
        paper_division_func=_to_paragraphs,
        reasoning=True,
    )


async def elicit_baseline_into_answer(paper: Paper, question: str, gold_support=None):
    gold_support  # unused
    texts = _to_paragraphs(paper)
    selections = await windowed_select_using_elicit_prompt(
        question=question, texts=texts
    )
    while selections:
        try:
            relevant_str = "\n\n".join([s[0] for s in selections])
            answer = await answer_like_elicit_qa(
                question=question, passage=relevant_str
            )
            answer_as_list = await quick_list(question=question, answer=answer)
            selection_set = set([s[0] for s in selections])
            return PaperQaAnswer(
                answer=answer_as_list,
                support_candidates=texts,
                support_labels=[text in selection_set for text in texts],
            )
        except TooLongRequestError:
            selections = remove_lowest_perplexity(selections)


async def elicit_baseline_prune_then_answer(
    paper: Paper, question: str, gold_support=None
):
    gold_support  # unused
    texts = _to_paragraphs(paper)
    selections = await windowed_select_using_elicit_prompt(
        question=question, texts=texts
    )
    while selections:
        try:
            pruned = await prune(
                question=question,
                texts=[s[0] for s in selections],
                max_to_keep=len(selections) // 2 if len(selections) > 10 else 5,
            )
            relevant_str = "\n\n".join(pruned)
            answer = await answer_like_elicit_qa(
                question=question, passage=relevant_str
            )
            answer_as_list = await quick_list(question=question, answer=answer)
            selection_set = set(pruned)
            return PaperQaAnswer(
                answer=answer_as_list,
                support_candidates=texts,
                support_labels=[text in selection_set for text in texts],
            )
        except TooLongRequestError:
            selections = remove_lowest_perplexity(selections)


async def decontext_elicit_baseline_prune_then_answer(
    paper: Paper, question: str, gold_support=None
):
    gold_support  # unused
    paper = await paper_decontext(paper)
    answer = await elicit_baseline_prune_then_answer(paper, question)
    assert answer


async def elicit_baseline_then_demonstration_answer(
    paper: Paper, question: str, gold_support=None
):
    gold_support  # unused
    texts = _to_paragraphs(paper)
    selections = await windowed_select_using_elicit_prompt(
        question=question, texts=texts

    )   
# while selections:
#     try:
#         return await cheating_few_shot_qa_baseline()
