from collections.abc import Sequence
from typing import Optional

from ice.recipes.meta.eval_text_classification import BinaryClassificationMetrics
from ice.recipes.meta.eval_text_classification import fuzzy_text_classification_metrics
from ice.recipes.meta.matching.match import match


async def eval_text_classification(
    candidates: Sequence[str],
    predictions: Sequence[bool],
    ground_truth: Sequence[str],
    scores: Optional[Sequence[float]] = None,
) -> BinaryClassificationMetrics:
    return await fuzzy_text_classification_metrics(
        texts=candidates,
        predictions=predictions,
        ground_truth=ground_truth,
        scores=scores,
    )


async def eval_sequence_gen(
    question: str,
    ground_truth: Sequence[str],
    prediction: Sequence[str],
) -> tuple[bool, str]:
    question  # unused
    eval_detail: str
    correct: bool
    if len(ground_truth) < len(prediction):
        eval_detail, correct = "Too many items", False
    elif len(ground_truth) > len(prediction):
        eval_detail, correct = "Too few items", False
    elif len(ground_truth) == 1:
        eval_detail, correct = "One item, assuming correct", True
    else:
        eval_detail, correct = await match(ground_truth, prediction)
    return correct, eval_detail
