from structlog.stdlib import get_logger

from ice.paper import Paper
from ice.paper import Paragraph
from ice.recipe import Recipe
from ice.recipes.rank_paragraphs import RankParagraphs

Experiment = str

log = get_logger()

DEFAULT_QUESTION_SHORT = (
    "What were the trial arms (subgroups of participants) of the experiment?"
)

DEFAULT_QUESTION_LONG = "What were the trial arms (subgroups of participants) of the experiment? List one per line."

DEFAULT_ANSWER_PREFIX = "Answer: The trial arms were:\n-"


def make_qa_prompt(
    question_short: str,
    question_long: str,
    answer_prefix: str,
    paragraphs: list[Paragraph],
) -> str:
    paragraphs_str = "\n\n".join(map(str, paragraphs))
    return f"""
Answer the question "{question_short}" based on the following paragraphs.

Paragraphs:

{paragraphs_str}

Question: {question_long}

{answer_prefix}
""".strip()


class ComparisonsQA(Recipe):
    async def run(
        self,
        paper: Paper,
        question_short: str = DEFAULT_QUESTION_SHORT,
        question_long: str = DEFAULT_QUESTION_LONG,
        num_paragraphs: int = 3,
        answer_prefix: str = DEFAULT_ANSWER_PREFIX,
    ):
        rank_paragraphs = RankParagraphs(mode=self.mode)

        top_paragraphs = await rank_paragraphs.run(
            paper=paper, question=question_short, n=num_paragraphs
        )

        qa_prompt = make_qa_prompt(
            question_short=question_short,
            question_long=question_long,
            answer_prefix=answer_prefix,
            paragraphs=top_paragraphs,
        )

        answer = await self.agent().complete(prompt=qa_prompt, max_tokens=500)

        return answer
