from typing import Optional

from structlog.stdlib import get_logger

from ice.recipe import Recipe
from ice.recipes.evaluate_result import EvaluateResult
from ice.recipes.evaluate_result import ResultComparison
from ice.utils import map_async

log = get_logger()


class EvaluateResults(Recipe):
    async def run(
        self,
        question: Optional[str] = None,
        model_results: Optional[list[str]] = None,
        gold_results: Optional[list[str]] = None,
    ) -> list[ResultComparison]:
        """
        Compare two lists of results, model and gold standard.
        """
        evaluate_result = EvaluateResult(mode=self.mode)

        if not model_results and not gold_results and not question:
            if not self.mode == "test":
                log.warning("No model results and no gold results - using test data.")
            model_results, gold_results, question = evaluate_result.test_data(n=3)
        elif not model_results or not gold_results or not question:
            raise ValueError("Must provide both model results and gold results.")

        comparisons = await map_async(
            list(zip(model_results, gold_results)),
            lambda pair: evaluate_result.run(
                question=question, model_result=pair[0], gold_result=pair[1]
            ),
            max_concurrency=self.max_concurrency(),
            show_progress_bar=True,
        )

        return comparisons
