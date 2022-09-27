from ice.recipes.primer.verify.utils import *

async def check_step(question: str, steps: list[str]) -> float:
    """
    Return the probability that the step is correct
    """
    prompt = make_verification_prompt(question=question, steps=steps)
    answer_probs, _ = await recipe.agent().classify(
        prompt=prompt, choices=[" Yes", " No"]
    )
    return answer_probs.get(" Yes", 0.0)

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
