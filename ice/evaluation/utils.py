from collections.abc import Sequence
from datetime import datetime

from ice.metrics.base import reduce_scores_dict
from ice.metrics.base import Sample
from ice.metrics.rouge import Rouge
from ice.metrics.rouge import RougeResult


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


def summarize_scores(scores: list[RougeResult]) -> RougeResult | None:
    if not scores:
        return None
    summary: dict[str, dict[str, float]] = dict()
    for metric in scores[0].dict(by_alias=True):
        summary[metric] = reduce_scores_dict(
            [score.dict(by_alias=True)[metric] for score in scores], mean
        )

    return RougeResult.parse_obj(summary)


start_time = datetime.now().astimezone()
