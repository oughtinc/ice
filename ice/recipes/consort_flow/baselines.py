from collections.abc import Callable
from collections.abc import Sequence
from functools import partial
from itertools import chain
from typing import Optional
from typing import Union

from ice.apis.openai import TooLongRequestError
from ice.metrics.gold_standards import get_gold_standard
from ice.metrics.gold_standards import load_papers
from ice.paper import Paper
from ice.recipe import recipe
from ice.recipes.consort_flow.baseline_elicit_answer import answer_like_elicit_qa
from ice.recipes.consort_flow.generate_questions import adherence_questions_and_answers
from ice.recipes.consort_flow.generate_questions import arms_questions_and_answers
from ice.recipes.consort_flow.generate_questions import (
    experiments_questions_and_answers,
)
from ice.recipes.consort_flow.types import ConsortFlow
from ice.recipes.experiments_and_arms.golds import get_ea_gs
from ice.recipes.meta.eval_paper_qa.common_baselines import (
    preselected_few_shot_qa_baseline,
)
from ice.recipes.meta.eval_paper_qa.quick_list import quick_list
from ice.recipes.meta.eval_paper_qa.types import PaperQaAnswer
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard
from ice.recipes.meta.eval_paper_qa.utils import convert_demonstration_example
from ice.recipes.program_search.nodes.decontext.decontextualize import paper_decontext
from ice.recipes.program_search.nodes.prune.prune import prune
from ice.recipes.program_search.nodes.prune.prune import prune_with_reasoning
from ice.recipes.program_search.nodes.select.select import (
    filter_by_perplexity_threshold,
)
from ice.recipes.program_search.nodes.select.select import (
    select_results_using_elicit_prompt,
)
from ice.recipes.program_search.nodes.select.select import (
    select_using_elicit_prompt_few_shot,
)
from ice.recipes.program_search.types import remove_lowest_perplexity


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
                experiments_questions_and_answers(paper, gs, consolidate=consolidate)
                for gs, paper in zip(gss, papers)
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
        [
            arms_questions_and_answers(paper, gs, consolidate=consolidate)
            for gs, paper in zip(gss, papers)
            if gs
        ]
    )
    used_gs = []
    for paper in paper_gs:
        for gs in paper:
            # 1 per paper
            used_gs.append(gs)
            break

    return used_gs


def adherence_few_shot_demonstration(
    document_id: str, consolidate: bool = False
) -> Sequence[PaperQaGoldStandard]:
    papers = [
        p
        for p in load_papers(split="validation", question_short_name="consort_flow_v2")
        if p.document_id != document_id
    ]
    gss = [
        get_gold_standard(
            document_id=p.document_id,
            question_short_name="consort_flow_v2",
            model_type=ConsortFlow,
        )
        for p in papers
    ]
    paper_gs = list(
        [
            adherence_questions_and_answers(paper, gs)
            for gs, paper in zip(gss, papers)
            if gs
        ]
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
    return await preselected_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=experiments_few_shot_demonstration,
    )


async def cheating_few_shot_qa_arms_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await preselected_few_shot_qa_baseline(
        paper,
        question,
        gold_support,
        enumerate_answer=True,
        few_shot_demonstration_func=arms_few_shot_demonstration,
    )


async def cheating_few_shot_qa_experiments_paragraph_baseline(
    paper: Paper, question: str, gold_support=None
):
    return await preselected_few_shot_qa_baseline(
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
    return await preselected_few_shot_qa_baseline(
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
    return await preselected_few_shot_qa_baseline(
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
    return await preselected_few_shot_qa_baseline(
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
    texts_with_perplexities = await select_results_using_elicit_prompt(
        question=question, texts=texts
    )
    # ~ .78 recall, .10 precision @ threshold=1.07
    selections = filter_by_perplexity_threshold(texts_with_perplexities, threshold=1.16)

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
                support_scores=[t[1] for t in texts_with_perplexities],
            )
        except TooLongRequestError:
            selections = remove_lowest_perplexity(selections)
    return PaperQaAnswer(
        answer=["The question is not answered in the text."],
        support_candidates=texts,
        support_labels=[False for text in texts],
        support_scores=[t[1] for t in texts_with_perplexities],
    )


async def _decontext_selections(paper: Paper, selections: Sequence[tuple[str, float]]):
    decontexted = await paper_decontext(paper)
    decontexted_paras = [str(p) for p in decontexted.paragraphs]
    original_paras = [str(p) for p in paper.paragraphs]
    assert len(decontexted_paras) == len(original_paras)
    old_to_new = {old: new for old, new in zip(original_paras, decontexted_paras)}
    return [(old_to_new[s[0]], s[1]) for s in selections]


async def _all_options(
    paper: Paper,
    question: str,
    gold_support: None,
    few_shot_demonstration_func: Callable[[str, bool], Sequence[PaperQaGoldStandard]],
    prune_to_max: Optional[int] = None,
    do_prune_reasoning: bool = False,
    do_few_shot_selection: bool = False,
    do_decontext_at_answer: bool = False,
    do_demonstration_answer: bool = False,
    do_demonstration_reasoning: bool = False,
    do_return_list: bool = True,
    cls_threshold: float = 1.06,
):
    gold_support  # unused
    texts = _to_paragraphs(paper)
    supporting_examples = few_shot_demonstration_func(paper.document_id, True)
    paragraph_supporting_examples = [
        await convert_demonstration_example(example, _to_paragraphs)
        for example in supporting_examples
    ]
    if do_few_shot_selection:
        texts_with_perplexities = await select_using_elicit_prompt_few_shot(
            question=question, texts=texts, examples=paragraph_supporting_examples
        )
        # Few-shot prompt needs a lower threshold
        selections = filter_by_perplexity_threshold(
            texts_with_perplexities,
            threshold=cls_threshold,
        )
    else:
        texts_with_perplexities = await select_results_using_elicit_prompt(
            question=question, texts=texts
        )
        selections = filter_by_perplexity_threshold(
            texts_with_perplexities,
            threshold=cls_threshold,
        )

    if prune_to_max:
        if do_prune_reasoning:
            pruned_selections = await prune_with_reasoning(
                question=question,
                texts_with_perplexities=selections,
                max_to_keep=prune_to_max,
            )
        else:
            pruned_selections = await prune(
                question=question,
                texts=[t[0] for t in selections],
                max_to_keep=prune_to_max,
            )

        selections = [t for t in selections if t[0] in pruned_selections]

    if do_decontext_at_answer:
        selections = await _decontext_selections(paper=paper, selections=selections)

    while selections:
        try:
            relevant_str = "\n\n".join([s[0] for s in selections])
            if not do_demonstration_answer:
                answer: Union[str, Sequence[str]] = await answer_like_elicit_qa(
                    question=question, passage=relevant_str
                )
                if do_return_list:
                    answer = await quick_list(question=question, answer=answer)  # type: ignore[arg-type]
            else:
                subrecipe_answer = await preselected_few_shot_qa_baseline(
                    paper=paper,
                    question=question,
                    gold_support=gold_support,
                    enumerate_answer=do_return_list,
                    few_shot_demonstration_func=lambda doc_id: few_shot_demonstration_func(
                        doc_id, not do_return_list
                    ),
                    selections=[s[0] for s in selections],
                    paper_division_func=_to_paragraphs,
                    reasoning=do_demonstration_reasoning,
                )
                answer = subrecipe_answer.answer
            selection_set = set([s[0] for s in selections])
            # support_labels = [text in selection_set for text in texts]
            # if not any(support_labels):
            #     breakpoint()
            return PaperQaAnswer(
                answer=answer,
                support_candidates=texts,
                support_labels=[text in selection_set for text in texts],
                support_scores=[t[1] for t in texts_with_perplexities],
            )
        except TooLongRequestError:
            selections = remove_lowest_perplexity(selections)
    return PaperQaAnswer(
        answer=["The question is not answered in the text."]
        if do_return_list
        else "The question is not answered in the text.",
        support_candidates=texts,
        support_labels=[False for text in texts],
        support_scores=[t[1] for t in texts_with_perplexities],
    )


zero_shot_arms_into_answer = partial(
    _all_options, few_shot_demonstration_func=arms_few_shot_demonstration
)
few_shot_arms_into_answer = partial(
    _all_options,
    do_few_shot_selection=True,
    few_shot_demonstration_func=arms_few_shot_demonstration,
)
elicit_prune_arms_reasoning_answer = partial(
    _all_options,
    few_shot_demonstration_func=arms_few_shot_demonstration,
    prune_to_max=7,
    do_prune_reasoning=True,
)
few_shot_arms_prune_reasoning_answer = partial(
    _all_options,
    few_shot_demonstration_func=arms_few_shot_demonstration,
    prune_to_max=7,
    do_few_shot_selection=True,
    do_prune_reasoning=True,
)
zero_shot_arms_few_shot_answer = partial(
    _all_options,
    few_shot_demonstration_func=arms_few_shot_demonstration,
    do_demonstration_answer=True,
)
zero_shot_arms_decontext_then_answer = partial(
    _all_options,
    few_shot_demonstration_func=arms_few_shot_demonstration,
    do_decontext_at_answer=True,
)
zero_shot_arms_decontext_few_shot_answer = partial(
    _all_options,
    few_shot_demonstration_func=arms_few_shot_demonstration,
    do_demonstration_answer=True,
    do_decontext_at_answer=True,
)

zero_shot_experiments_into_answer = partial(
    _all_options, few_shot_demonstration_func=experiments_few_shot_demonstration
)
few_shot_experiments_into_answer = partial(
    _all_options,
    do_few_shot_selection=True,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
)
elicit_prune_experiments_reasoning_answer = partial(
    _all_options,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
    prune_to_max=7,
    do_prune_reasoning=True,
)
few_shot_experiments_prune_reasoning_answer = partial(
    _all_options,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
    prune_to_max=7,
    do_few_shot_selection=True,
    do_prune_reasoning=True,
)
zero_shot_experiments_few_shot_answer = partial(
    _all_options,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
    do_demonstration_answer=True,
)
zero_shot_experiments_few_shot_answer_with_reasoning = partial(
    _all_options,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
    do_demonstration_answer=True,
    do_demonstration_reasoning=True,
)


zero_shot_experiments_decontext_then_answer = partial(
    _all_options,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
    do_decontext_at_answer=True,
)
zero_shot_experiments_decontext_few_shot_answer = partial(
    _all_options,
    few_shot_demonstration_func=experiments_few_shot_demonstration,
    do_demonstration_answer=True,
    do_decontext_at_answer=True,
)


zero_shot_adherence_into_answer = partial(
    _all_options,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    do_return_list=False,
)
few_shot_adherence_into_answer = partial(
    _all_options,
    do_few_shot_selection=True,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    do_return_list=False,
)
elicit_prune_adherence_reasoning_answer = partial(
    _all_options,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    prune_to_max=7,
    do_prune_reasoning=True,
    do_return_list=False,
)
few_shot_adherence_prune_reasoning_answer = partial(
    _all_options,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    prune_to_max=7,
    do_few_shot_selection=True,
    do_prune_reasoning=True,
    do_return_list=False,
)
zero_shot_adherence_few_shot_answer = partial(
    _all_options,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    do_demonstration_answer=True,
    do_return_list=False,
)
zero_shot_adherence_decontext_then_answer = partial(
    _all_options,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    do_decontext_at_answer=True,
    do_return_list=False,
)
zero_shot_adherence_decontext_few_shot_answer = partial(
    _all_options,
    few_shot_demonstration_func=adherence_few_shot_demonstration,
    do_demonstration_answer=True,
    do_decontext_at_answer=True,
    do_return_list=False,
)


async def elicit_baseline_prune_then_answer(
    paper: Paper, question: str, gold_support=None
):
    gold_support  # unused
    texts = _to_paragraphs(paper)
    selections = await select_results_using_elicit_prompt(
        question=question, texts=texts
    )
    texts_with_perplexities = await select_results_using_elicit_prompt(
        question=question, texts=texts
    )
    # ~ .78 recall, .10 precision @ threshold=1.07
    selections = filter_by_perplexity_threshold(texts_with_perplexities, threshold=1.16)
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
                support_scores=[t[1] for t in texts_with_perplexities],
            )
        except TooLongRequestError:
            selections = remove_lowest_perplexity(selections)
    return PaperQaAnswer(
        answer=["The question is not answered in the text."],
        support_candidates=texts,
        support_labels=[False for _ in texts],
        support_scores=[t[1] for t in texts_with_perplexities],
    )


async def decontext_elicit_baseline_prune_then_answer(
    paper: Paper, question: str, gold_support=None
):
    gold_support  # unused
    paper = await paper_decontext(paper)
    answer = await elicit_baseline_prune_then_answer(paper, question)
    assert answer


recipe.main(elicit_baseline_into_answer)
