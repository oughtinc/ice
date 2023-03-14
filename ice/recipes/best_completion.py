import math
from functools import partial

from structlog.stdlib import get_logger

from ice.apis.openai import openai_complete
from ice.recipe import recipe
from ice.utils import map_async

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

    tokens = choices[0]["logprobs"]["tokens"]
    completion_tokens: list[str] = []
    for token in reversed(tokens):
        if completion.endswith("".join(completion_tokens)):
            completion_tokens = [token] + completion_tokens
        else:
            break

    completion_tokens = (
        completion_tokens[1:]
        if completion == "".join(completion_tokens[1:])
        else completion_tokens
    )
    if completion != "".join(completion_tokens):
        print("".join(completion_tokens), completion)

    completion_logits = logits[-len(completion_tokens) :]

    perplexity = math.exp(-sum(completion_logits) / len(completion_logits))

    return perplexity


async def best_completion(
    prompts: list[str] = PROMPTS,
    completion: str = COMPLETION,
) -> list[tuple[str, float]]:
    """Returns a list of prompts and their perplexities."""
    perplexities = await map_async(
        input_list=prompts,
        fn=partial(completion_perplexity, completion=completion),
        max_concurrency=10,
    )
    return list(zip(prompts, perplexities))


recipe.main(best_completion)
