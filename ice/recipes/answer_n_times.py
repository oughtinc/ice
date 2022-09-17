from structlog import get_logger

from ice.recipe import Recipe
from ice.recipes.tutorial_amplification import AmplifiedQA
from ice.recipes.rank_paragraphs import RankParagraphs


log = get_logger()


class AnswerNTimes(Recipe):
    async def run(
        self,
        question: str = "What is the effect of creatine on cognition?",
        depth = 1,
        attempts: int = 2,
        return_all = False
    ):
        """
        Depth: how many levels of question decomposition to recurse to
        Attempts: repeat the question process this many times. Why attempt more than once? If you have a temperature > 0, simply repeating the process might yield different results."""
        answers = []
        for attempt in range(attempts):
            answers.append(AmplifiedQA.run(question, depth))
        
        if return_all:
            return answers
        
        grouped_answers = '\n'.join(answers)
        return RankParagraphs(grouped_answers, question, 1)[0]
