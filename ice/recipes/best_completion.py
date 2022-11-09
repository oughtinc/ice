import math

from functools import partial

from structlog.stdlib import get_logger

from ice.apis.openai import openai_complete
from ice.recipe import recipe
from ice.utils import map_async
from ice.utils import n_tokens

log = get_logger()

PROMPTS = [
    "The Golden Gate bridge is in",
    "The Statue of Liberty is in",
    "The Eiffel Tower is in",
]

COMPLETION = " San Francisco, California, USA"


async def completion_perplexity(
    prompt: str = PROMPTS[0],
    completion: str = COMPLETION,
) -> float:
    """Calculate the perplexity of a completion given a prompt."""
    if not completion[0].isspace():
        log.warning("Completion does not start with whitespace!", completion=completion)
    response = await openai_complete(
        prompt=prompt + completion,
        max_tokens=0,
        logprobs=1,
        echo=True,
    )

    choices = response.get("choices", [])

    if not choices:
        raise ValueError("No choices returned from OpenAI API")

    logits = choices[0]["logprobs"]["token_logprobs"]

    completion_logits = logits[n_tokens(prompt) :]

    perplexity = math.exp(-sum(completion_logits) / len(completion_logits))

    return perplexity


async def best_completion(
    prompts: list[str] = PROMPTS,
    completion: str = COMPLETION,
) -> list[tuple[str, float]]:
    """Returns a sorted list of completions and their perplexities."""
    perplexities = await map_async(
        input_list=prompts,
        fn=partial(completion_perplexity, completion=completion),
        max_concurrency=10,
    )
    prompt_list = list(zip(prompts, perplexities))

    return sorted(prompt_list, key=lambda x: x[1])


recipe.main(best_completion)
