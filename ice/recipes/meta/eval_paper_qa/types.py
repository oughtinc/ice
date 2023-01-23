from collections.abc import Sequence
from dataclasses import dataclass
from typing import Generic
from typing import Optional
from typing import Protocol
from typing import TypeVar

from ice.paper import Paper
from ice.recipes.meta.eval_text_classification import BinaryClassificationMetrics

AnswerType_contra = TypeVar("AnswerType_contra", contravariant=True)


@dataclass
class PaperQaGoldStandard(Generic[AnswerType_contra]):
    paper: Paper
    question: str
    gold_answer: AnswerType_contra
    short_gold_answer: AnswerType_contra
    gold_support: Sequence[str]


@dataclass
class PaperQaAnswer(Generic[AnswerType_contra]):
    answer: AnswerType_contra
    support_candidates: Sequence[str]
    support_labels: Sequence[bool]
    support_scores: Optional[Sequence[float]] = None


@dataclass
class SequenceGenerationEvaluation(Generic[AnswerType_contra]):
    document_id: str
    question: str
    correct: bool
    detail: str
    metrics: BinaryClassificationMetrics
    gold_answer: AnswerType_contra
    generated_answer: AnswerType_contra
    support: Sequence[str]
    generation_f1_score: float

    def as_dict(self):
        return dict(
            document_id=self.document_id,
            question=self.question,
            correct=self.correct,
            detail=self.detail,
            metrics=self.metrics.as_dict(),
            gold_answer=repr(self.gold_answer),
            generated_answer=repr(self.generated_answer),
            support=self.support,
            f1_score=self.generation_f1_score,
        )


class PaperQaMethod(Protocol[AnswerType_contra]):
    async def __call__(
        self,
        __paper: Paper,
        __question: str,
        __gold_support: Optional[Sequence[str]] = None,
    ) -> PaperQaAnswer[AnswerType_contra]:
        ...


class AnswerEvalMethod(Protocol[AnswerType_contra]):
    async def __call__(
        self,
        question: str,
        ground_truth: AnswerType_contra,
        prediction: AnswerType_contra,
    ) -> tuple[bool, str]:
        ...


class ClassificationEvalMethod(Protocol):
    async def __call__(
        self,
        candidates: Sequence[str],
        predictions: Sequence[bool],
        ground_truth: Sequence[str],
        scores: Optional[Sequence[float]] = None,
    ) -> BinaryClassificationMetrics:
        ...
