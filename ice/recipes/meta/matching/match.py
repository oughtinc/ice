


from typing import Sequence

from ice.recipes.meta.matching.prompt import MATCHING_STOP_SEQUENCES, matching_prompt, reasoning_and_answer_from_completion
from ice.recipe import recipe


async def match(items_a: Sequence[str], items_b: Sequence[str]) -> tuple[str, bool]:
    assert len(items_a) == len(items_b), "Matching intended only for sequences of equal length"
    prompt = matching_prompt(items_a, items_b)
    completion = await recipe.agent().complete(prompt=prompt, stop=MATCHING_STOP_SEQUENCES)
    reasoning, answer = reasoning_and_answer_from_completion(completion)
    return reasoning, answer


recipe.main(match)
