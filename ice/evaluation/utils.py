from collections.abc import Sequence
from datetime import datetime
from typing import Optional

from ice.metrics.base import reduce_scores_dict
from ice.metrics.base import Sample
from ice.metrics.rouge import Rouge
from ice.metrics.rouge import RougeResult
from ice.settings import OUGHT_ICE_DIR

CSVS_PATH = OUGHT_ICE_DIR / "evaluation_csvs/"


def _partial_confusion_matrix(
    actuals: list[bool], predictions: list[bool]
) -> tuple[int, int, int]:
    assert len(actuals) == len(predictions)
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    for actual, prediction in zip(actuals, predictions):
        if actual and prediction:
            true_positives += 1
        elif not actual and prediction:
            false_positives += 1
        elif actual and not prediction:
            false_negatives += 1
    return true_positives, false_positives, false_negatives


def precision_score(actuals: list[bool], predictions: list[bool]) -> float:
    true_positives, false_positives, _ = _partial_confusion_matrix(actuals, predictions)
    return (
        true_positives / (true_positives + false_positives) if true_positives else 0.0
    )


def recall_score(actuals: list[bool], predictions: list[bool]) -> float:
    true_positives, _, false_negatives = _partial_confusion_matrix(actuals, predictions)
    return (
        true_positives / (true_positives + false_negatives) if true_positives else 0.0
    )


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def top(values: list[float]) -> float:
    return max(values) if values else 0.0


async def rouge_compare(hyp: Sequence[str], ref: Sequence[str]) -> RougeResult:
    sample = Sample(left=hyp, right=ref)
    rouge = Rouge()
    scores = await rouge.compute([sample])
    assert len(scores) == 1
    return scores[0]


def summarize_scores(scores: list[RougeResult]) -> Optional[RougeResult]:
    if not scores:
        return None
    summary: dict[str, dict[str, float]] = dict()
    for metric in scores[0].dict(by_alias=True):
        summary[metric] = reduce_scores_dict(
            [score.dict(by_alias=True)[metric] for score in scores], mean
        )

    return RougeResult.parse_obj(summary)


start_time = datetime.now().astimezone()
