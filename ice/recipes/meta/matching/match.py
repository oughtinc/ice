from collections.abc import Sequence

from ice.recipe import recipe
from ice.recipes.meta.matching.prompt import matching_prompt
from ice.recipes.meta.matching.prompt import MATCHING_STOP_SEQUENCES
from ice.recipes.meta.matching.prompt import reasoning_and_answer_from_completion


async def match(items_a: Sequence[str], items_b: Sequence[str]) -> tuple[str, bool]:
    assert len(items_a) == len(
        items_b
    ), "Matching intended only for sequences of equal length"
    prompt = matching_prompt(items_a, items_b)
    completion = await recipe.agent("alpha-current").complete(
        prompt=prompt,
        stop=MATCHING_STOP_SEQUENCES,
        max_tokens=600,
    )
    reasoning, answer = reasoning_and_answer_from_completion(completion)
    return reasoning, answer


recipe.main(match)
