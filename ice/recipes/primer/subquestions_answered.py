from fvalues import F

from ice.recipe import recipe
from ice.recipes.primer.subquestions import ask_subquestions
from ice.utils import map_async


def make_qa_prompt(question: str) -> str:
    return F(
        f"""Answer the following question:

Question: "{question}"
Answer: "
"""
    ).strip()


async def answer(question: str) -> str:
    prompt = make_qa_prompt(question)
    answer = await recipe.agent().complete(prompt=prompt, stop='"')
    return answer


async def answer_by_amplification(
    question: str = "What is the effect of creatine on cognition?",
):
    subquestions = await ask_subquestions(question=question)
    subanswers = await map_async(subquestions, answer)
    return list(zip(subquestions, subanswers))


recipe.main(answer_by_amplification)
