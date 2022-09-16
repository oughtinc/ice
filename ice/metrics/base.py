from collections.abc import Callable
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic
from typing import TypeVar

Reducer = Callable[[list[float]], float]


def reduce_scores_dict(
    scores: list[dict[str, float]], reducer: Reducer
) -> dict[str, float]:
    return {k: reducer([score[k] for score in scores]) for k in scores[0]}


@dataclass
class Sample:
    """
    Two lists of inputs to be compared via a metric.

    For example, left could be a list of hypothesis generations
    and right some reference (gold standard) examples.

    Or left could be human-generated examples and right could be
    GPT-generated examples.
    """

    left: Sequence[str]
    right: Sequence[str]

    def __post_init__(self):
        if not self.left or not self.right:
            raise ValueError("Each sample must have at least one element")

    def identical_sample(self):
        return set(self.left) == set(self.right)


RetVal = TypeVar("RetVal")


class Metric(Generic[RetVal]):
    async def compute(self, samples: list[Sample]) -> list[RetVal]:
        raise NotImplementedError
