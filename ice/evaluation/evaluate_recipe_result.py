from collections.abc import Callable
from collections.abc import Sequence
from statistics import mean
from typing import Optional

from pydantic import BaseModel

from ice.evaluation.utils import rouge_compare
from ice.metrics.gold_standards import get_gold_standard
from ice.metrics.gold_standards import GoldStandard
from ice.settings import settings
from ice.utils import map_async


class MatchResult(BaseModel):
    text: str
    found: bool


class EvaluatedExcerpts(BaseModel):
    gold_standards_in_excerpts_results: Sequence[MatchResult]
    excerpts: Sequence[str]
    average_recall: Optional[float]

    @classmethod
    async def from_excerpts_and_gold_quotes(
        cls,
        excerpts: Sequence[str],
        gold_quotes: Sequence[str],
    ) -> "EvaluatedExcerpts":
        all_excerpts = " |||| ".join(excerpts)

        gold_standards_scores = await map_async(
            gold_quotes,
            lambda gold_standard: rouge_compare([all_excerpts], [gold_standard]),
        )

        gold_standards_recalls = [score.rouge_l.r for score in gold_standards_scores]

        gold_standards_found = [
            recall > settings.GS_QUOTE_FOUND_THRESHOLD
            for recall in gold_standards_recalls
        ]

        overall_recall = (
            mean(gold_standards_recalls) if gold_standards_recalls else None
        )

        return cls(
            gold_standards_in_excerpts_results=[
                MatchResult(text=gold_standard, found=found)
                for gold_standard, found in zip(gold_quotes, gold_standards_found)
            ],
            excerpts=excerpts,
            average_recall=overall_recall,
        )

    def summary_stats_str(self) -> str:
        if not self.excerpts:
            return "The recipe didn't find any excerpts. This usually means that the recipe didn't try to find excerpts and instead answered by reading the whole paper."

        found_count = len(
            [
                gold_standard
                for gold_standard in self.gold_standards_in_excerpts_results
                if gold_standard.found
            ]
        )
        total_count = len(self.gold_standards_in_excerpts_results)
        proportion = self.proportion_gold_standards_found
        return f"""The recipe found {found_count}/{total_count}{' (' + f'{proportion:.0%}' + ')' if proportion is not None else ''} gold standard excerpts."""

    def gold_standards_str(self) -> str:
        return "\n".join(
            f"{i+1}. {'(Found by recipe)' if gold_standard_match.found else '(Not found by recipe)'} {gold_standard_match.text}"
            for i, gold_standard_match in enumerate(
                self.gold_standards_in_excerpts_results
            )
        )

    def excerpts_str(self) -> str:
        if self.excerpts:
            return "\n\nRecipe excerpts:\n\n" + "\n".join(
                f"{i}. {excerpt}" for i, excerpt in enumerate(self.excerpts, 1)
            )
        return ""

    def __str__(self) -> str:
        return f"""{self.summary_stats_str()}

Gold standard excerpts:

{self.gold_standards_str()}{self.excerpts_str()}

Average ROUGE-L recall across all gold standards (for debugging): {self.average_recall}
"""

    @property
    def num_gold_standards_found(self) -> Optional[int]:
        if len(self.gold_standards_in_excerpts_results) == 0:
            return None
        return len(
            [
                gold_standard
                for gold_standard in self.gold_standards_in_excerpts_results
                if gold_standard.found
            ]
        )

    @property
    def proportion_gold_standards_found(self) -> Optional[float]:
        num_gold_standards_found = self.num_gold_standards_found
        if (
            num_gold_standards_found is None
            or len(self.gold_standards_in_excerpts_results) == 0
        ):
            return None
        return num_gold_standards_found / len(self.gold_standards_in_excerpts_results)


class EvaluatedClassification(BaseModel):
    predicted: Optional[str]
    gold: Optional[str]
    classification_eq: Optional[
        Callable[[Optional[str], Optional[str]], Optional[bool]]
    ]

    @property
    def is_correct(self) -> Optional[bool]:
        if self.classification_eq is None:
            if self.gold is None:
                return None
            return self.predicted == self.gold
        else:
            return self.classification_eq(self.predicted, self.gold)

    def __str__(self) -> str:
        correctness = (
            "Correct"
            if self.is_correct == True
            else "Incorrect"
            if self.is_correct == False
            else "Not evaluated"
        )
        return f"""{correctness}.
    - Predicted: {self.predicted}
    - Gold: {self.gold}"""


class RecipeResult(BaseModel):
    question_short_name: str
    document_id: str
    answer: str
    experiment: str
    excerpts: Sequence[str]
    result: Optional[object] = None
    classifications: Sequence[Optional[str]] = []
    classification_eq: Sequence[
        Optional[Callable[[Optional[str], Optional[str]], Optional[bool]]]
    ] = []
    elicit_commit: Optional[str]
    answer_rating: Optional[int]
    failure_modes: Optional[Sequence[str]]


class EvaluatedRecipeResult(RecipeResult):
    evaluated_excerpts: EvaluatedExcerpts
    gold_standard: Optional[GoldStandard]

    @classmethod
    async def from_recipe_result(
        cls, recipe_result: RecipeResult
    ) -> "EvaluatedRecipeResult":
        gold_standard = get_gold_standard(
            document_id=recipe_result.document_id,
            question_short_name=recipe_result.question_short_name,
            experiment=recipe_result.experiment,
        )
        return cls(
            gold_standard=gold_standard,
            evaluated_excerpts=await EvaluatedExcerpts.from_excerpts_and_gold_quotes(
                excerpts=recipe_result.excerpts,
                gold_quotes=gold_standard.quotes if gold_standard else [],
            ),
            **recipe_result.dict(),
        )

    @property
    def evaluated_classifications(self) -> list[EvaluatedClassification]:
        recipe_classifications = self.classifications
        gold_classifications = (
            self.gold_standard.classifications if self.gold_standard else []
        )

        evaluated_classifications = []

        for i in range(0, max(len(recipe_classifications), len(gold_classifications))):
            evaluated_classification = EvaluatedClassification(
                predicted=recipe_classifications[i]
                if i < len(recipe_classifications)
                else None,
                gold=gold_classifications[i] if i < len(gold_classifications) else None,
                classification_eq=self.classification_eq[i]
                if i < len(self.classification_eq)
                else None,
            )

            evaluated_classifications.append(evaluated_classification)

        return evaluated_classifications

    def answer_str(self) -> str:
        return f"""- Answer: {self.answer}
- Gold standard: {self.gold_standard.answer if self.gold_standard else 'n/a'}
"""

    def classifications_str(self) -> str:
        return "\n".join(
            [
                f"- Classification {i+1}: {evaluated_classification}"
                for i, evaluated_classification in enumerate(
                    self.evaluated_classifications
                )
            ]
        )

    def __str__(self) -> str:
        return f"""
## {self.document_id} / {self.question_short_name} / {self.experiment}

### Answer

{self.answer_str()}

### Classifications

{self.classifications_str()}

### Finding excerpts

{self.evaluated_excerpts}
"""
