from ice.recipe import recipe
from ice.recipes.primer.verify.last import check_step
from ice.recipes.primer.verify.utils import *
from ice.utils import map_async


async def verify_answer(
    question: str = DEFAULT_QUESTION, steps: list[str] = DEFAULT_STEPS
):
    """
    For each prefix of 1..n steps, check if the nth step is correct.
    """
    step_indices = list(range(1, len(steps) + 1))
    step_probs = await map_async(
        step_indices,
        lambda index: check_step(question=question, steps=steps[:index]),
    )
    return list(zip(step_probs, steps))


recipe.main(verify_answer)
