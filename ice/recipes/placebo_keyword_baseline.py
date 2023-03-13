import re
from dataclasses import dataclass
from typing import Literal

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import Paper
from ice.recipe import Recipe

PlaceboClassification = Literal["Placebo", "Not mentioned", "No placebo", "Unclear"]


@dataclass
class PlaceboAnswer:
    classification: PlaceboClassification
    sentence: str


class PlaceboKeywordBaseline(Recipe):
    @staticmethod
    def answer_placebo_using_keywords(paper: Paper) -> PlaceboAnswer:
        """
        1. first, if the paper says it's open-label (matches `open[- ](control|label)`), classify as "No placebo"
            a. return the 1st sentence that matches as the quote supporting this answer
        2. then, if we didn't classify as "No placebo" based on the previous step, then check if the world "placebo" is in the paper. If so, classify as "Placebo"
            a. return the 1st sentence that contains "placebo" as the quote supporting this answer as well as the description of the placebo/the answer
        3. then, if we haven't found anything yet, classify as "Not mentioned"
            a. don't return any supporting quote
        """
        sentences = [
            sentence
            for paragraph in paper.paragraphs
            for sentence in paragraph.sentences
        ]
        for sentence in sentences:
            if re.search("open[- ](control|label)", sentence, re.IGNORECASE):
                return PlaceboAnswer("No placebo", sentence)
        for sentence in sentences:
            if re.search("placebo", sentence, re.IGNORECASE):
                return PlaceboAnswer("Placebo", sentence)
        return PlaceboAnswer("Not mentioned", "")

    async def run(self, paper: Paper):
        experiments = list_experiments(document_id=paper.document_id)

        results: list[RecipeResult] = []
        for experiment in experiments:
            placebo_answer = self.answer_placebo_using_keywords(paper)
            results.append(
                RecipeResult(
                    experiment=experiment,
                    question_short_name="placebo",
                    document_id=paper.document_id,
                    result=f"{placebo_answer.classification}: {placebo_answer.sentence}",
                    answer=f"{placebo_answer.classification}: {placebo_answer.sentence}",
                    classifications=[
                        "Placebo"
                        if placebo_answer.classification == "Placebo"
                        else "No placebo or placebo not mentioned",
                        placebo_answer.classification,
                    ],
                    excerpts=[placebo_answer.sentence],
                )
            )

        self.maybe_add_to_results(results)

        return results
