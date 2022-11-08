from typing import Protocol, Sequence, Mapping
from ice.paper import Paper
from dataclasses import dataclass

from ice.recipes.meta.eval_text_classification import BinaryClassificationMetrics

@dataclass
class PaperQaGoldStandard:
    paper: Paper
    question: str
    gold_answer: Sequence[str] | str
    gold_support: Sequence[str]

@dataclass
class PaperQaAnswer:
    answer: str | Sequence[str]
    support_candidates: Sequence[str]
    support_labels: Sequence[bool]

@dataclass
class SequenceGenerationEvaluation:
    correct: bool
    detail: str
    metrics: BinaryClassificationMetrics
    gold_answer: str | Sequence[str]
    generated_answer: str | Sequence[str]


class PaperQaMethod(Protocol):
    async def __call__(
        self,
        __paper: Paper,
        __question: str,
        __gold_support: Sequence[str] | None = None,
    ) -> PaperQaAnswer:
        ...