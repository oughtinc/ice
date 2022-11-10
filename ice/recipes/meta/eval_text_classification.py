from itertools import chain
from typing import Iterable, Sequence, Mapping
from dataclasses import dataclass
from functools import cached_property
import numpy as np

from ice.metrics.rouge import matches


@dataclass(frozen=True)
class BinaryClassificationMetrics:
    ground_truth: Sequence[bool]
    predictions: Sequence[bool]

    def __post_init__(self):
        assert len(self.ground_truth) == len(
            self.predictions
        ), "Ground truth and predictions should have the same length"

    @cached_property
    def _gt_array(self):
        return np.array(self.ground_truth, dtype=bool)

    @cached_property
    def _pred_array(self):
        return np.array(self.predictions, dtype=bool)

    @cached_property
    def tp(self):
        return (self._gt_array & self._pred_array).sum()

    @cached_property
    def tn(self):
        return (~self._gt_array & ~self._pred_array).sum()

    @cached_property
    def fn(self):
        return (self._gt_array & ~self._pred_array).sum()

    @cached_property
    def fp(self):
        return (~self._gt_array & self._pred_array).sum()

    @cached_property
    def recall(self):
        return self.tp / (self.tp + self.fn) if self.tp or self.fn else 0

    @cached_property
    def precision(self):
        return self.tp / (self.tp + self.fp) if self.tp or self.fn else 0

    @cached_property
    def f1(self):
        return (
            2 * (self.precision * self.recall) / (self.precision + self.recall)
            if self.precision or self.recall
            else 0
        )

    @cached_property
    def accuracy(self):
        return (self._gt_array == self._pred_array).mean() if self.ground_truth else 0

    def as_dict(self) -> dict[str, int | float]:
        return dict(
            tp=int(self.tp),
            tn=int(self.tn),
            fp=int(self.fp),
            fn=int(self.fn),
            recall=float(self.recall),
            precision=float(self.precision),
            f1=float(self.f1),
            accuracy=float(self.accuracy),
        )

    def __str__(self):
        return str(self.as_dict())

    def __repr__(self):
        return f"<BinaryClassificiationMetrics {str(self)}>"

    @classmethod
    def aggregate(
        cls, metrics: Iterable["BinaryClassificationMetrics"]
    ) -> "BinaryClassificationMetrics":
        ms = list(metrics)
        return cls(
            ground_truth=list(chain(*(m.ground_truth for m in ms))),
            predictions=list(chain(*(m.predictions for m in ms))),
        )


async def label_texts(
    texts: Sequence[str], golds: Sequence[str], lcs_threshold: float = 0.7
) -> Sequence[bool]:
    gs_matches: set[str] = set()
    for gold in golds:
        gs_matches = gs_matches.union(
            (
                await matches(
                    hypotheses=texts, references=[gold], lcs_threshold=lcs_threshold
                )
            ).keys()
        )
    return [text in gs_matches for text in texts]


async def fuzzy_text_classification_metrics(
    texts: Sequence[str],
    predictions: Sequence[bool],
    ground_truth: Sequence[str],
    lcs_threshold: float = 0.7,
) -> BinaryClassificationMetrics:
    """Because labeled ground truths are often partial excerpts, use Rouge lcs-recall of ground truth to generate labels.

    Args:
        texts (Sequence[str]): The texts in question
        predictions (Sequence[bool]): Labels to evaluate
        ground_truth (Sequence[str]): The positive strings to be matched with texts using rouge-lcs-recall

    Returns:
        BinaryClassificationMetrics: Metrics
    """
    gt_labels = await label_texts(texts, ground_truth, lcs_threshold=lcs_threshold)
    return BinaryClassificationMetrics(ground_truth=gt_labels, predictions=predictions)
