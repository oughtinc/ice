from collections.abc import Sequence
from typing import Generic
from typing import Optional

from pydantic.generics import GenericModel

from ice.recipes.program_search.utils.find_examples import mark_gs
from ice.recipes.program_search.utils.find_examples import rouge_distractor_scores
from ice.recipes.program_search.utils.find_examples import SelectionT_co
from ice.utils import window_dropping


class SelectionExample(GenericModel, Generic[SelectionT_co]):
    selection: Sequence[SelectionT_co]
    existing: Sequence[str]
    positive_idxs: Sequence[int]
    distractor_score: float


async def make_examples(
    texts: Sequence[SelectionT_co],
    gs_quotes: Sequence[str],
    *,
    n: int,
    step: int,
    max_existing: int,
) -> Sequence[SelectionExample]:
    gs_labeled = await mark_gs(texts, gs_quotes)
    gs_texts = {str(text) for text in gs_labeled if text.is_gs}
    windowed = window_dropping(gs_labeled, n, step)
    examples: list[SelectionExample] = []
    for window in windowed:
        # TODO: Consider different orderings?
        positive_idxs = [idx for idx, text in enumerate(window) if text.is_gs]
        existing = list(gs_texts - {str(text) for text in window})[:max_existing]
        distractor_scores = await rouge_distractor_scores(
            [text.original for text in window], references=gs_quotes
        )
        summary_distractor_score = (
            sum(distractor_scores.values()) / len(distractor_scores)
            if distractor_scores
            and not any(score == 0 for score in distractor_scores.values())
            else 0
        )
        examples.append(
            SelectionExample(
                selection=window,
                existing=existing,
                positive_idxs=positive_idxs,
                distractor_score=summary_distractor_score,
            )
        )
    return examples


def first_positive_example(
    examples: Sequence[SelectionExample],
) -> Optional[SelectionExample]:
    try:
        return next(
            filter(
                lambda example: example.positive_idxs,
                examples,
            )
        )
    except StopIteration:
        return None


def best_negative_example(
    examples: Sequence[SelectionExample],
) -> Optional[SelectionExample]:
    negative_examples = list(
        filter(lambda example: not example.positive_idxs, examples)
    )
    if not negative_examples:
        return None
    return max(negative_examples, key=lambda example: example.distractor_score)
