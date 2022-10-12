from structlog import get_logger

from ice.recipe import AmplifiedQA
from ice.recipe import Recipe
from ice.utils import map_async


log = get_logger()


def make_summary_prompt(passage: str, background: str) -> str:
    if background is None:
        background_text = ""
    else:
        background_text = f"""The following is a summarization task. Here is some relevant background to guide you: {background}"""
    return f"""{background_text}Summarize the following passage, using the background information above where helpful:
{passage}
Answer: "
""".strip()


class SummarizeNTimes(Recipe):
    async def run(
        self,
        passage: str = "blah blah blah, long passage to summarize. maybe try summarizing 2 or 3 paragraphs together? like the two proceeding the most-relevant paragraph and then putting that summary and the most relevant paragraph together through the next process step?",
        background: str = None,
        attempts: int = 1,
    ):
        """Why attempt n times? If you have a temperature > 0, simply repeating the process might yield different results."""
        summaries = []
        prompt = make_summary_prompt(passage, background)
        for attempt in range(attempts):
            answer = (await self.agent().answer(prompt=prompt, max_tokens=100)).strip(
                '" '
            )
            summaries.append(answer)

        return summaries
