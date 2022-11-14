from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Iterable, Mapping, Sequence, Protocol
from ice.apis.openai import TooLongRequestError
from ice.formatter.transform.value import numbered_list
from ice.metrics.gold_standards import GoldStandard, ModelType
from ice.paper import Paper
from ice.recipe import recipe
from ice.recipes.meta.eval_paper_qa.quick_list import quick_list
from ice.recipes.meta.eval_paper_qa.utils import download_papers
from ice.recipes.meta.eval_paper_qa.quick_question_driven_eval import quick_eval
from ice.recipes.meta.matching.match import match
from ice.recipes.meta.eval_text_classification import (
    BinaryClassificationMetrics,
    fuzzy_text_classification_metrics,
)
from ice.recipes.primer.paper_qa import answer_for_paper
from ice.recipes.meta.eval_paper_qa.types import (
    PaperQaAnswer,
    PaperQaGoldStandard,
    SequenceGenerationEvaluation,
    PaperQaMethod,
)
from ice.recipes.primer.qa import answer
from ice.recipes.program_search.nodes.answer.answer import (
    Demonstration,
    demonstration_answer,
    demonstration_answer_with_reasoning,
)
from ice.recipes.program_search.nodes.select.select import (
    windowed_select_using_elicit_prompt,
    windowed_select_using_scibert,
)
from ice.recipes.program_search.utils.find_examples import identify_gs_str, mark_gs
from ice.trace import trace
from ice.utils import map_async

def to_paragraphs(paper: Paper) -> Sequence[str]:
    return [str(p) for p in paper.paragraphs]

async def eval_unstructured_list(
    ground_truth: Sequence[str], predictions: Sequence[str]
) -> tuple[str, bool]:
    return await match(ground_truth, predictions)


async def eval_text_classification(
    candidates: Sequence[str], predictions: Sequence[bool], ground_truth: Sequence[str]
) -> BinaryClassificationMetrics:
    return await fuzzy_text_classification_metrics(
        texts=candidates, predictions=predictions, ground_truth=ground_truth
    )


async def eval_sequence_gen_task(
    ground_truth: Sequence[str],
    predictions: Sequence[str],
    support_candidates: Sequence[str],
    support_labels: Sequence[bool],
    ground_truth_support: Sequence[str],
):
    eval_detail: str
    correct: bool
    if len(ground_truth) < len(predictions):
        eval_detail, correct = "Too many items", False
    elif len(ground_truth) > len(predictions):
        eval_detail, correct = "Too few items", False
    elif len(ground_truth) == 1:
        eval_detail, correct = "One item, assuming correct", True
    else:
        eval_detail, correct = await match(ground_truth, predictions)
    classification_metrics = await eval_text_classification(
        candidates=support_candidates,
        predictions=support_labels,
        ground_truth=ground_truth_support,
    )
    return SequenceGenerationEvaluation(
        correct=correct,
        detail=eval_detail,
        metrics=classification_metrics,
        gold_answer=ground_truth,
        generated_answer=predictions,
    )


async def paper_qa_baseline(
    paper: Paper, question, gold_support: Sequence[str] | None, enumerate_answer: bool
) -> PaperQaAnswer:
    gold_support  # unused TODO: does the method really need this?
    answer: str | Sequence[str]
    all_paras = [str(p).casefold().strip() for p in paper.paragraphs if str(p).strip()]
    answer, predicted_paras = await answer_for_paper(paper, question, top_n=1)
    predicted_paras = [p.casefold().strip() for p in predicted_paras]
    if enumerate_answer:
        answer = await quick_list(question, answer)
    return PaperQaAnswer(
        answer=answer,
        support_candidates=all_paras,
        support_labels=[p.casefold().strip() in predicted_paras for p in all_paras],
    )


async def cheating_qa_baseline(
    paper: Paper,
    question: str,
    gold_support: Sequence[str] | None,
    enumerate_answer: bool,
):
    relevant_str = "\n\n".join(gs for gs in gold_support) if gold_support else ""
    if not relevant_str:
        raise ValueError("Method requires gold support")
    response = await answer(context=relevant_str, question=question)
    if enumerate_answer:
        response = await quick_list(question, response)
    assert gold_support
    return PaperQaAnswer(
        answer=response,
        support_candidates=gold_support,
        support_labels=[True for _ in gold_support],
    )

async def search_qa_baseline(
    paper: Paper,
    question: str,
    gold_support: Sequence[str] | None,
    gold_support_func: Callable[[str], Sequence[PaperQaGoldStandard]],
):
    excerpts = to_paragraphs(paper)

    other_gs = gold_support_func(paper.document_id)

    examples = await map_async(
        input_list=other_gs,
        fn=partial(convert_demonstration_example, paper_division_func=to_paragraphs),
    )

    relevant_excerpts = await windowed_select_using_scibert(
        question=question,
        texts=excerpts,
        examples=examples,
    )
    relevant_str = "\n\n".join(relevant_excerpts)
    response = ""#await answer(context=relevant_str, question=question)
    assert gold_support
    return PaperQaAnswer(
        answer=response,
        support_candidates=excerpts,
        support_labels=[e in relevant_excerpts for e in excerpts],
    )

async def convert_demonstration_example(
    example: PaperQaGoldStandard,
    paper_division_func: Callable[[Paper], Sequence[str]],
) -> PaperQaGoldStandard:
    paper_parts = paper_division_func(example.paper)
    return PaperQaGoldStandard(
        paper=example.paper,
        question=example.question,
        gold_answer=example.gold_answer,
        gold_support=(await identify_gs_str(paper_parts, example.gold_support)),
    )


async def few_shot_qa_with_support(
    paper: Paper,
    question: str,
    support_labels: Sequence[bool],
    support_candidates: Sequence[str],
    enumerate_answer: bool,
    gold_support_func: Callable[[str], Sequence[PaperQaGoldStandard]],
    paper_division_func: Callable[[Paper], Sequence[str]] | None = None,
    reasoning: bool = False,
):
    demonstration_examples = gold_support_func(paper.document_id)
    if paper_division_func:
        demonstration_examples = await map_async(
            demonstration_examples,
            partial(
                convert_demonstration_example,
                paper_division_func=paper_division_func,
            ),
        )
    demonstration_examples = [ex for ex in demonstration_examples if ex.gold_support][
        :3
    ]

    demonstrations = [
        Demonstration(
            question=g.question,
            texts=g.gold_support,
            answer=g.gold_answer
            if isinstance(g.gold_answer, str)
            else numbered_list(g.gold_answer).transform(),
        )
        for g in demonstration_examples
    ]

    answer = await _demonstration_answer(
        question=question,
        texts=[cand for lab, cand in zip(support_labels, support_candidates) if lab],
        demonstrations=demonstrations,
        reasoning=reasoning,
    )

    if enumerate_answer:
        answer = await quick_list(question, answer)
    return PaperQaAnswer(
        answer=answer,
        support_candidates=support_candidates,
        support_labels=support_labels,
    )


async def _demonstration_answer(
    question: str,
    texts: Sequence[str],
    demonstrations: Sequence[Demonstration],
    reasoning: bool,
):
    try:
        if not reasoning:
            return await demonstration_answer(
                question=question, texts=texts, demonstrations=demonstrations
            )
        else:
            return await demonstration_answer_with_reasoning(
                question=question, texts=texts, demonstrations=demonstrations
            )
    except TooLongRequestError:
        demonstrations = demonstrations[:-1]
        if len(demonstrations) < 1:
            raise
        return await _demonstration_answer(
            question=question,
            texts=texts,
            demonstrations=demonstrations,
            reasoning=reasoning,
        )


async def cheating_few_shot_qa_baseline(
    paper: Paper,
    question: str,
    gold_support: Sequence[str] | None,
    enumerate_answer: bool,
    gold_support_func: Callable[[str], Sequence[PaperQaGoldStandard]],
    paper_division_func: Callable[[Paper], Sequence[str]] | None = None,
    reasoning: bool = False,
):
    demonstration_examples = gold_support_func(paper.document_id)
    if paper_division_func:
        demonstration_examples = await map_async(
            demonstration_examples,
            partial(
                convert_demonstration_example,
                paper_division_func=paper_division_func,
            ),
        )
    demonstration_examples = [ex for ex in demonstration_examples if ex.gold_support][
        :3
    ]
    demonstrations = [
        Demonstration(
            question=g.question,
            texts=g.gold_support,
            answer=g.gold_answer
            if isinstance(g.gold_answer, str)
            else numbered_list(g.gold_answer).transform(),
        )
        for g in demonstration_examples
    ]
    assert gold_support
    if paper_division_func:
        gold_support = await identify_gs_str(paper_division_func(paper), gold_support)
    assert gold_support  # somehow required here to satisfy mypy ???
    answer = await _demonstration_answer(
        question=question,
        texts=gold_support,
        demonstrations=demonstrations,
        reasoning=reasoning,
    )

    if enumerate_answer:
        answer = await quick_list(question, answer)
    return PaperQaAnswer(
        answer=answer,
        support_candidates=gold_support,
        support_labels=[True for _ in gold_support],
    )


async def eval_method(
    method: PaperQaMethod,
    question_and_answer_func: Callable[
        [GoldStandard[ModelType]], Iterable[PaperQaGoldStandard]
    ],
    split: str,
    question_short_name: str,
    get_gs=Callable[[str], GoldStandard[ModelType] | None],
    max_concurrency: int = 10,
):

    papers = download_papers(split, question_short_name=question_short_name)

    @trace
    async def run_eval(
        input_data: tuple[Paper, PaperQaGoldStandard]
    ) -> SequenceGenerationEvaluation:
        paper, qa_details = input_data
        answer = await method(paper, qa_details.question, qa_details.gold_support)
        if isinstance(answer.answer, str):
            # assert isinstance(qa_details.gold_answer, str)
            # correct = await quick_eval(
            #     question=qa_details.question,
            #     gold=qa_details.gold_answer,
            #     generated=answer.answer,
            # )
            metrics = await eval_text_classification(
                candidates=answer.support_candidates,
                predictions=answer.support_labels,
                ground_truth=qa_details.gold_support,
            )
            return SequenceGenerationEvaluation(
                correct=True,#correct,
                detail="",
                metrics=metrics,
                generated_answer=answer.answer,
                gold_answer=qa_details.gold_answer,
            )
        else:
            assert not isinstance(qa_details.gold_answer, str)
            evaluation = await eval_sequence_gen_task(
                ground_truth=qa_details.gold_answer,
                predictions=answer.answer,
                support_candidates=answer.support_candidates,
                support_labels=answer.support_labels,
                ground_truth_support=qa_details.gold_support,
            )
            return evaluation

    eval_data: list[tuple[Paper, PaperQaGoldStandard]] = []
    gold_supports: list[Sequence[str]] = []

    for paper in papers:
        gold = get_gs(paper.document_id)
        if not gold:
            continue
        for gs_detail in question_and_answer_func(gold):
            eval_data.append((paper, gs_detail))
            gold_supports.append(gs_detail.gold_support)

    results = await map_async(eval_data, run_eval, max_concurrency=max_concurrency)

    scores = [r.correct for r in results]
    metrics = [r.metrics for r in results]

    # only aggregate where there is gold support (somewhat arbitrary choice but more informative)
    metrics_under_support = [m for m, gs in zip(metrics, gold_supports) if gs]
    aggregated_metrics = BinaryClassificationMetrics.aggregate(metrics_under_support)

    return (
        sum(scores) / len(scores) if scores else 0,
        results,
        aggregated_metrics.as_dict(),
    )


recipe.main(eval_method)
