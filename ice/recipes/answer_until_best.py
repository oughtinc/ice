from structlog import get_logger

from ice.recipe import Recipe
from ice.recipes.answer_n_times import AnswerNTimes
from ice.recipies.rank_paragraphs import RankParagraphs


log = get_logger()


class AnswerUntilBest(Recipe):
    async def run(
        self,
        question: str = "What is the effect of creatine on cognition?",
        max_depth=10,
        attempts_per_level: int = 2,
    ):
        """
        Max_Depth: how many levels of question decomposition to recurse to at maximum
        Attempts_per_level: repeat the question process this many times at each level of depth, and return the best according to rank_paragraphs. Why attempt more than once? If you have a temperature > 0, simply repeating the process might yield different results."""
        best_answer = None
        for depth in range(1, max_depth + 1):
            current_answer = AnswerNTimes.run(
                question, depth=depth, attempts=attempts_per_level
            )
            if best_answer is None:
                best_answer = current_answer
            else:
                grouped_answers = "\n".join([best_answer, current_answer])
                new_best_answer = RankParagraphs(grouped_answers, question, 1)[0]
                if best_answer == new_best_answer:
                    break

        return best_answer
