from structlog import get_logger

from ice.recipe import Recipe
from ice.recipes.rank_paragraphs import RankParagraphs
from ice.recipes.summarize_n_times import SummarizeNTimes

log = get_logger()


class SummarizeUntilBest(Recipe):
    async def run(
        self,
        passage: str = "blah blah blah, long passage to summarize. maybe try summarizing 2 or 3 paragraphs together? like the two proceeding the most-relevant paragraph and then putting that summary and the most relevant paragraph together through the next process step?",
        background: str = None,
        attempts_per_cycle: int = 2,
        max_cycles: int = 5,
    ):
        """
        Max_Depth: how many levels of question decomposition to recurse to at maximum
        Attempts_per_level: repeat the question process this many times at each level of depth, and return the best according to rank_paragraphs. Why attempt more than once? If you have a temperature > 0, simply repeating the process might yield different results.
        """
        best_summary = None
        for cycle in range(1, max_cycles + 1):
            current_summaries = SummarizeNTimes.run(
                passage, background=background, attempts=attempts_per_cycle
            )
            if best_summary is None:
                grouped_summaries = "\n".join(current_summaries)
                best_summary = RankParagraphs(
                    grouped_summaries, "", 1, prompt_type="summary"
                )[0]
            else:
                grouped_summaries = "\n".join([best_summary] + current_summaries)
                new_best_summary = RankParagraphs(
                    grouped_summaries, "", 1, prompt_type="summary"
                )[0]
                if best_summary == new_best_summary:
                    break

        return best_summary
