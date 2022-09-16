import re

from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import list_experiments
from ice.paper import Paper
from ice.recipe import Recipe

SEARCH_TERMS = ["adhere", "take-up", "compliance", "attrition"]


class AdherenceKeywordBaseline(Recipe):
    @staticmethod
    def answer_adherence_using_keywords(paper: Paper) -> str:
        for term in SEARCH_TERMS:
            for paragraph in paper.paragraphs:
                paragraph_text = " ".join(paragraph.sentences)
                if re.search(term, paragraph_text):
                    return paragraph_text
        return ""

    async def run(self, paper: Paper):
        experiments = list_experiments(document_id=paper.document_id)

        results: list[RecipeResult] = []
        for experiment in experiments:
            answer = self.answer_adherence_using_keywords(paper)
            results.append(
                RecipeResult(
                    experiment=experiment,
                    question_short_name="adherence",
                    document_id=paper.document_id,
                    answer=answer,
                    classifications=[None, None],
                    excerpts=[answer],
                )
            )

        self.maybe_add_to_results(results)

        return results
