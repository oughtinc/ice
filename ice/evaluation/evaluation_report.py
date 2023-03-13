from collections.abc import Sequence
from dataclasses import dataclass
from statistics import mean
from typing import Optional
from typing import Union

import pandas as pd
from pydantic import BaseModel
from rich import box
from rich.table import Table

from ice.evaluation.evaluate_recipe_result import EvaluatedRecipeResult
from ice.evaluation.utils import CSVS_PATH
from ice.evaluation.utils import precision_score
from ice.evaluation.utils import recall_score
from ice.evaluation.utils import start_time
from ice.utils import latest_commit_hash

SUBSTANTIVELY_CORRECT_MIN_ANSWER_RATING = 4


def as_percent(decimal: Optional[float]) -> Optional[str]:
    if decimal is None:
        return None
    return "{:.0%}".format(decimal)


@dataclass
class ClassificationSummary:
    num_correct: int
    num_evaluated: int
    classification_options: set[str]

    @property
    def proportion_correct(self) -> Optional[float]:
        if self.num_evaluated == 0:
            return None

        return self.num_correct / self.num_evaluated

    def labels_str(self) -> str:
        return ", ".join(list(self.classification_options))


@dataclass
class AnsweredWhenShouldHaveSummary:
    gs_should_answer: list[bool]
    answered: list[bool]

    @property
    def precision(self) -> float:
        if not self.gs_should_answer:
            return 0.0
        return precision_score(self.gs_should_answer, self.answered)

    @property
    def recall(self) -> float:
        if not self.gs_should_answer:
            return 0.0
        return recall_score(self.gs_should_answer, self.answered)

    @property
    def proportion_of_gs_where_should_answer(self) -> float:
        return len(
            [should_answer for should_answer in self.gs_should_answer if should_answer]
        ) / (len(self.gs_should_answer) or 1)


class EvaluationReport(BaseModel):
    technique_name: str
    results: Sequence[EvaluatedRecipeResult]

    @property
    def mean_proportion_gs_found_across_papers(self) -> Optional[float]:
        paper_scores = [
            result.evaluated_excerpts.proportion_gold_standards_found
            for result in self.results
            if result.evaluated_excerpts.proportion_gold_standards_found is not None
        ]

        if len(paper_scores) == 0:
            return None
        return float(mean(paper_scores))

    @property
    def proportion_papers_with_gs_found(self) -> Optional[float]:
        gs_found = [
            result.evaluated_excerpts.num_gold_standards_found > 0
            for result in self.results
            if result.evaluated_excerpts.num_gold_standards_found is not None
        ]

        if len(gs_found) == 0:
            return None

        return mean(gs_found)

    @property
    def classification_summaries(self) -> list[ClassificationSummary]:
        classification_summaries = []

        for i in range(
            0,
            max([len(result.evaluated_classifications) for result in self.results]),
        ):
            is_corrects = []

            for result in self.results:
                try:
                    is_corrects.append(result.evaluated_classifications[i].is_correct)
                except IndexError:
                    continue

            evaluations = [
                is_correct for is_correct in is_corrects if is_correct is not None
            ]

            classification_summaries.append(
                ClassificationSummary(
                    num_correct=sum(evaluations),
                    num_evaluated=len(evaluations),
                    classification_options=self.classification_options(i),
                )
            )

        return classification_summaries

    @property
    def answered_when_should_have(self) -> AnsweredWhenShouldHaveSummary:
        results_to_eval = [
            result for result in self.results if result.gold_standard is not None
        ]
        gs_should_answer = [
            False if result.gold_standard.answer == "" else True  # type: ignore
            for result in results_to_eval
        ]
        answered = [
            False if result.answer == "" else True for result in results_to_eval
        ]

        return AnsweredWhenShouldHaveSummary(
            gs_should_answer=gs_should_answer,
            answered=answered,
        )

    @property
    def elicit_commit(self):
        elicit_commits = list(set([result.elicit_commit for result in self.results]))
        if len(elicit_commits) > 1:
            raise ValueError("Attempting to evaluate multiple Elicit commits at once")
        return elicit_commits[0]

    @property
    def answer_ratings(self):
        return [
            result.answer_rating
            for result in self.results
            if result.answer_rating is not None
        ]

    @property
    def answers_rated(self):
        return len(self.answer_ratings)

    @property
    def average_answer_rating(self):
        return mean(self.answer_ratings) if len(self.answer_ratings) > 0 else None

    @property
    def proportion_of_answers_rated_correct(self):
        return (
            (
                len(
                    [
                        answer_rating
                        for answer_rating in self.answer_ratings
                        if answer_rating >= SUBSTANTIVELY_CORRECT_MIN_ANSWER_RATING
                    ]
                )
                / len(self.answer_ratings)
            )
            if self.answer_ratings
            else None
        )

    @property
    def failure_modes(self):
        # TODO: use more_itertools.flatten instead
        all_failure_modes = []
        for result in self.results:
            if result.failure_modes is None:
                continue
            for failure_mode in result.failure_modes:
                all_failure_modes.append(failure_mode)

        if not all_failure_modes:
            return None

        return pd.Series(all_failure_modes).value_counts().to_string()

    def classification_options(self, classification_idx=int) -> set[str]:
        classification_options: set[str] = set()

        for result in self.results:
            try:
                gold_classification = result.evaluated_classifications[
                    classification_idx
                ].gold
                if gold_classification is not None:
                    classification_options.add(gold_classification)
            except IndexError:
                continue

        return classification_options

    def questions_str(self) -> str:
        questions = list(set([result.question_short_name for result in self.results]))
        return ", ".join(questions)

    def classification_summary_stats_str(self) -> str:
        return "\n".join(
            [
                (
                    f"- Classification {i+1}:"
                    + "\n    - proportion correct: "
                    + (
                        f"{classification_summary.proportion_correct:.0%} ({classification_summary.num_correct} / {classification_summary.num_evaluated})"
                        if classification_summary.proportion_correct is not None
                        else "Nothing to evaluate"
                    )
                    + f"\n    - labels: {classification_summary.labels_str()}"
                )
                for i, classification_summary in enumerate(
                    self.classification_summaries
                )
            ]
        )

    def make_comparison_table(
        self,
        document_id_rows: list[str],
        gold_standard_rows: list[str],
        model_rows: list[str],
    ) -> Table:
        table = Table(width=120, box=box.MARKDOWN)
        table.add_column("Document", no_wrap=True)
        table.add_column("Gold Standard")
        table.add_column("Model")

        for did, gs, mr in zip(document_id_rows, gold_standard_rows, model_rows):
            table.add_row(str(did), str(gs), str(mr))

        return table

    def description_results_table(self) -> Table:
        document_ids = []
        gold_standard_descriptions = []
        model_descriptions = []
        for result in self.results:
            gold_standard = result.gold_standard
            if gold_standard is not None:
                if gold_standard.answer != gold_standard.classifications[0]:
                    document_ids.append(gold_standard.document_id)
                    gold_standard_descriptions.append(gold_standard.answer)
                    model_descriptions.append(result.answer)
        return self.make_comparison_table(
            document_ids, gold_standard_descriptions, model_descriptions
        )

    def classification_results_table(self) -> Table:
        document_ids = []
        gold_standard_classifications = []
        model_classifications = []
        for result in self.results:
            gold_standard = result.gold_standard
            if gold_standard is not None:
                document_ids.append(gold_standard.document_id)
                gold_standard_classifications.append(
                    gold_standard.classifications[1] or ""
                )
                model_classification = (
                    result.classifications[0] if result.classifications else ""
                )
                model_classifications.append(model_classification or "")
        return self.make_comparison_table(
            document_ids, gold_standard_classifications, model_classifications
        )

    def excerpts_summary_stats_str(self) -> str:
        s = ""
        if self.mean_proportion_gs_found_across_papers:
            s += f"### Average % of gold standards found: \n\n{self.mean_proportion_gs_found_across_papers:.0%}"
        if self.proportion_papers_with_gs_found:
            s += f"\n\n### Proportion of papers with at least one gold standard found: \n\n{self.proportion_papers_with_gs_found:.0%}"
        if not s:
            s = "n/a"
        return s

    def precision_recall_str(self) -> str:
        return f"""- precision: {self.answered_when_should_have.precision:.0%}
- recall: {self.answered_when_should_have.recall:.0%}
- (proportion of gold standards where should answer: {self.answered_when_should_have.proportion_of_gs_where_should_answer:.0%})
"""

    def to_rich_elements(self) -> list[Union[str, Table]]:
        return [
            f"""
# Performance on papers

{"---".join(str(r) for r in self.results)}

# Summary of results

## Classifications:
""",
            self.classification_results_table(),
            """
## Descriptions:
""",
            self.description_results_table(),
            """
## Classification summary stats:
""",
            self.classification_summary_stats_str(),
            """
## Excerpts summary stats:
""",
            self.excerpts_summary_stats_str(),
            """
## Answered when should have:
""",
            self.precision_recall_str(),
        ]

    def __str__(self) -> str:
        return "\n".join(str(e) for e in self.to_rich_elements())

    def make_dashboard_row_df(self):
        CSVS_PATH.mkdir(parents=True, exist_ok=True)

        questions = self.questions_str()
        row = {
            "Questions": questions,
            "Technique": self.technique_name,
            "Eval date": start_time,
            "Elicit commit": self.elicit_commit,
            "ICE commit": latest_commit_hash(),
            "Splits": ", ".join(
                set(
                    result.gold_standard.split
                    for result in self.results
                    if result.gold_standard and result.gold_standard.split
                )
            ),
            "# of results": len(self.results),
            "Papers with >= 1 GS quote found": as_percent(
                self.proportion_papers_with_gs_found
            ),
            "Mean % of GS quotes found": as_percent(
                self.mean_proportion_gs_found_across_papers
            ),
            "Precision (answer if should)": as_percent(
                self.answered_when_should_have.precision
            ),
            "Recall (answer if should)": as_percent(
                self.answered_when_should_have.recall
            ),
            "% GS where should answer": as_percent(
                self.answered_when_should_have.proportion_of_gs_where_should_answer
            ),
            "Answers rated": self.answers_rated,
            "Average answer rating": self.average_answer_rating,
            "% answers rated substantively correct": as_percent(
                self.proportion_of_answers_rated_correct
            ),
            "Failure mode counts": self.failure_modes,
        }
        for i, classification_summary in enumerate(self.classification_summaries):
            row[f"Classification {i+1} labels"] = classification_summary.labels_str()

            row[f"Classification {i+1} correct"] = as_percent(
                classification_summary.proportion_correct
            )

            row[
                f"Classification {i+1} # evaluated"
            ] = classification_summary.num_evaluated

        df = pd.DataFrame([row])
        df.to_csv(
            CSVS_PATH / f"dashboard_row {start_time} {questions}.csv",
            index=False,
        )
        return df

    def make_experiments_evaluation_df(self):
        CSVS_PATH.mkdir(parents=True, exist_ok=True)

        rows = []
        questions = self.questions_str()

        for result in self.results:
            row = {
                "question_short_name": result.question_short_name,
                "technique": self.technique_name,
                "eval_date": start_time,
                "elicit_commit": result.elicit_commit,
                "ice_commit": latest_commit_hash(),
                "document_id": result.document_id,
                "split": result.gold_standard.split if result.gold_standard else None,
                "experiment": result.gold_standard.experiment
                if result.gold_standard
                else None,
                "total_gs_quotes": len(
                    result.evaluated_excerpts.gold_standards_in_excerpts_results
                ),
                "gs_quotes_found": result.evaluated_excerpts.num_gold_standards_found,
                "proportion_gs_quotes_found": result.evaluated_excerpts.proportion_gold_standards_found,
                "evaluated_excerpts": str(result.evaluated_excerpts),
                "excerpts": result.evaluated_excerpts.excerpts,
                "gs_quotes": result.evaluated_excerpts.gold_standards_str(),
                "answer": result.answer,
                "gs_answer": result.gold_standard.answer
                if result.gold_standard
                else None,
                "answer_rating": result.answer_rating,
                "failure_modes": result.failure_modes,
            }

            if result.gold_standard:
                row["gs_answer"] = result.gold_standard.answer
                row["should_answer"] = result.gold_standard.answer != ""
                row["answered"] = result.answer != ""

            for i, classification in enumerate(result.evaluated_classifications):
                row[f"classification_{i+1}_correct"] = classification.is_correct
                row[f"classification_{i+1}"] = classification.predicted
                row[f"gold_classification_{i+1}"] = classification.gold

            rows.append(row)
        df = pd.DataFrame(rows)
        df.to_csv(
            CSVS_PATH / f"experiments_evaluation {start_time} {questions}.csv",
            index=False,
        )
        return df
