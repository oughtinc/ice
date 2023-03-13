from collections.abc import Iterable
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from typing import Optional
from typing import Union

import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import PrecisionRecallDisplay
from sklearn.metrics import roc_auc_score

from ice.metrics.rouge import matches


@dataclass(frozen=True)
class BinaryClassificationMetrics:
    ground_truth: Sequence[bool]
    predictions: Sequence[bool]
    scores: Optional[Sequence[float]] = None

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
        return (self._gt_array & self._pred_array).sum().item()

    @cached_property
    def tn(self):
        return (~self._gt_array & ~self._pred_array).sum().item()

    @cached_property
    def fn(self):
        return (self._gt_array & ~self._pred_array).sum().item()

    @cached_property
    def fp(self):
        return (~self._gt_array & self._pred_array).sum().item()

    @cached_property
    def recall(self):
        return self.tp / (self.tp + self.fn) if self.tp or self.fn else 0

    @cached_property
    def precision(self):
        return self.tp / (self.tp + self.fp) if self.tp or self.fp else 0

    @cached_property
    def f1(self):
        return (
            2 * (self.precision * self.recall) / (self.precision + self.recall)
            if self.precision or self.recall
            else 0
        )

    @cached_property
    def accuracy(self):
        return (
            (self._gt_array == self._pred_array).mean().item()
            if self.ground_truth
            else 0
        )

    @cached_property
    def auroc(self):
        if not self.scores:
            return None
        if not any(self.ground_truth):
            return None
        return roc_auc_score(y_true=self._gt_array, y_score=self.scores)

    def save_pr_curve(self, filename: str):
        if not self.scores:
            return None
        prd = PrecisionRecallDisplay.from_predictions(
            y_true=self._gt_array, y_pred=self.scores
        )
        prd.plot()
        plt.savefig(filename)

    def pr_thresholds(self, n: Optional[int] = 20):
        if not self.scores:
            return None
        precisions, recalls, thresholds = precision_recall_curve(
            y_true=self._gt_array, probas_pred=self.scores
        )
        n = min(n or len(thresholds), len(thresholds))
        idxs = np.linspace(0, len(thresholds), n, endpoint=False).astype(int)
        return {
            float(t): dict(p=float(p), r=float(r))
            for p, r, t in zip(precisions[idxs], recalls[idxs], thresholds[idxs])
        }

    def as_dict(self) -> dict[str, Optional[Union[int, float]]]:
        return dict(
            tp=int(self.tp),
            tn=int(self.tn),
            fp=int(self.fp),
            fn=int(self.fn),
            recall=float(self.recall),
            precision=float(self.precision),
            f1=float(self.f1),
            accuracy=float(self.accuracy),
            auroc=self.auroc and float(self.auroc),
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
        do_scores = all((m.scores is not None for m in ms))
        return cls(
            ground_truth=list(chain(*(m.ground_truth for m in ms))),
            predictions=list(chain(*(m.predictions for m in ms))),
            scores=list(chain(*(m.scores or [] for m in ms))) if do_scores else None,
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
    scores: Optional[Sequence[float]] = None,
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
    return BinaryClassificationMetrics(
        ground_truth=gt_labels, predictions=predictions, scores=scores
    )
