from collections.abc import Mapping
from collections.abc import Sequence

from structlog.stdlib import get_logger

from ice.apis.openai import openai_complete
from ice.recipe import recipe
from ice.recipes.program_search.nodes.prune.prompts import EXAMPLE_SEPARATOR
from ice.recipes.program_search.nodes.prune.prompts import (
    get_pruned_selections_via_logprobs,
)
from ice.recipes.program_search.nodes.prune.prompts import make_pruning_prompt
from ice.recipes.program_search.nodes.prune.prompts import (
    make_pruning_with_reasoning_prompt,
)
from ice.recipes.program_search.types import remove_lowest_perplexity
from ice.utils import n_tokens

log = get_logger()


# class Select(Protocol):
#     async def __call__(self, question: str, texts: list[str], examples: list[Example]) -> list[int]:
#         pass


def last_token_logprob(openai_response: dict) -> float:
    return openai_response["choices"][0]["logprobs"]["token_logprobs"][-1]


def last_token_top_logprobs(openai_response: dict) -> dict[str, float]:
    return openai_response["choices"][0]["logprobs"]["top_logprobs"][-1]


def logprobs_greater_than_none(
    selections: Mapping[int, float], none_logprob: float, texts: Sequence[str]
) -> Sequence[str]:
    return [text for idx, text in enumerate(texts) if selections[idx] > none_logprob]


async def prune(question: str, texts: list[str], max_to_keep: int) -> list[str]:
    prompt = make_pruning_prompt(question=question, existing=texts)
    response = await openai_complete(
        prompt=prompt, max_tokens=80, logprobs=100, echo=False, stop=EXAMPLE_SEPARATOR
    )
    selection_probs = get_pruned_selections_via_logprobs(
        response["choices"][0]["logprobs"], num_selections=len(texts)
    )
    selections = sorted(selection_probs, key=selection_probs.__getitem__, reverse=True)[
        :max_to_keep
    ]
    return [texts[selection] for selection in selections]


async def prune_with_reasoning(
    question: str,
    texts_with_perplexities: Sequence[tuple[str, float]],
    max_to_keep: int,
) -> list[str]:
    # todo: compare first logprob method to completion parse method
    if max_to_keep > 5:
        log.warning(
            "the openai api only returns the top 5 logprobs, so we cannot keep more than 5 candidates via logprobs.",
            num_candidates=len(texts_with_perplexities),
        )
    prompt = make_pruning_with_reasoning_prompt(
        question=question, existing=[t[0] for t in texts_with_perplexities]
    )
    while n_tokens(prompt) > 3200:
        texts_with_perplexities = remove_lowest_perplexity(texts_with_perplexities)
        prompt = make_pruning_with_reasoning_prompt(
            question=question, existing=[t[0] for t in texts_with_perplexities]
        )
    response = await openai_complete(
        prompt=prompt,
        max_tokens=4000 - n_tokens(prompt),
        logprobs=100,
        echo=False,
        stop=EXAMPLE_SEPARATOR,
    )
    completion: str = response["choices"][0]["text"]
    if "from most to least important: " not in completion:
        log.warning("Unexpected completion", prompt=prompt, completion=completion)
        prompt = (
            prompt
            + completion.rstrip()
            + "\n\nWhich excerpts answer the question, from most to least"
        )
        response = await openai_complete(
            prompt=prompt,
            max_tokens=4090 - n_tokens(prompt),
            logprobs=100,
            echo=False,
            stop=EXAMPLE_SEPARATOR,
        )

    selection_probs = get_pruned_selections_via_logprobs(
        response["choices"][0]["logprobs"], num_selections=len(texts_with_perplexities)
    )
    selections = sorted(selection_probs, key=selection_probs.__getitem__, reverse=True)[
        :max_to_keep
    ]
    texts = [t[0] for t in texts_with_perplexities]
    return [texts[selection] for selection in selections]


recipe.main(prune)
