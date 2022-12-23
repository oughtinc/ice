from fvalues import F

from ice.recipe import recipe
from ice.recipes.primer.verify.utils import *


def make_verification_prompt(question: str, steps: list[str]) -> str:
    return F(
        f"""Consider this question: "{question}"

Here are the first few steps of an answer:

{render_steps(steps)}

Q: Is step {len(steps)} correct, assuming that the previous steps are correct? Say "A: Yes" or "A: No".
A:"""
    )


async def check_step(question: str, steps: list[str]) -> float:
    """
    Return the probability that the step is correct
    """
    prompt = make_verification_prompt(question=question, steps=steps)
    answer_probs, _ = await recipe.agent().classify(
        prompt=prompt, choices=(" Yes", " No")
    )
    return answer_probs.get(" Yes", 0.0)


async def verify_answer(
    question: str = DEFAULT_QUESTION, steps: list[str] = DEFAULT_STEPS
):
    return await check_step(question=question, steps=steps)


recipe.main(verify_answer)
