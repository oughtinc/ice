from structlog import get_logger

from ice.recipe import Recipe
from ice.recipe import AmplifiedQA
from ice.utils import map_async


log = get_logger()


def make_summary_prompt(statement: str, background: str) -> str:
    if background is None:
        background_text = ''
    else:
        background_text =  f"""The following is a rephrasing task. Here is some relevant background to guide you: {background}"""
    return f"""{background_text}Please rephrase the following statement to make it more scientific and have clear logical flow. Each premise in the reasoning should be explained. Statement: {statement}""".strip()


class RephraseNTimes(Recipe):
    async def run(
        self,
        passage: str = "What is the effect of creatine on cognition?",
        n_times: int = 1,
        background: str = None,
        return_all = False
    ):
        prompt = make_summary_prompt(passage, background)
        answer = (await self.agent().answer(prompt=prompt, max_tokens=100)).strip('" ')
        return answer


