from ice.evaluation.evaluate_recipe_result import RecipeResult
from ice.metrics.gold_standards import get_gold_standard
from ice.metrics.gold_standards import list_experiments
from ice.paper import Paper
from ice.recipe import Recipe


class AllQuotesRecipe(Recipe):
    # Used to view paper parses
    # and to test whether the gold standard quotes we're looking for
    # are actually in the parses
    question_short_name_to_test = "placebo"

    async def run(self, paper: Paper):
        experiments = list_experiments(document_id=paper.document_id)

        results: list[RecipeResult] = []
        for experiment in experiments:
            gold_standard = get_gold_standard(
                document_id=paper.document_id,
                question_short_name=self.question_short_name_to_test,
                experiment=experiment,
            )

            if gold_standard:
                results.append(
                    RecipeResult(
                        experiment=experiment,
                        question_short_name=self.question_short_name_to_test,
                        document_id=paper.document_id,
                        answer="",
                        classifications=[],
                        excerpts=[
                            paragraph.__str__() for paragraph in paper.paragraphs
                        ],
                    )
                )

        self.maybe_add_to_results(results)

        return results
