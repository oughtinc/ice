from typing import Mapping, Protocol, Sequence, cast
from typing_extensions import reveal_type
from ice.apis.openai import TooLongRequestError, openai_complete
from ice.paper import Paper
from ice.recipe import Recipe, recipe
from ice.recipes.program_search.nodes.prune.prompts import EXAMPLE_SEPARATOR, get_pruned_selections_via_completion, get_pruned_selections_via_logprobs, make_pruning_prompt
from ice.utils import reduce_async, window_dropping
from structlog.stdlib import get_logger

from ice.recipes.program_search.nodes.select.prompts import (
    get_selections,
    make_selection_prompt,
)

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


async def prune(
    question: str, texts: list[str], max_to_keep: int
) -> list[str]:
    # TODO: Compare first logprob method to completeion parse method
    if max_to_keep > 5:
        log.warning(
            "The OpenAI API only returns the top 5 logprobs, so we cannot keep more than 5 candidates via logprobs.",
            num_candidates=len(texts),
        )
    prompt = make_pruning_prompt(question=question, existing=texts)
    response = await openai_complete(
        prompt=prompt, max_tokens=80, logprobs=100, echo=False, stop=EXAMPLE_SEPARATOR
    )
    selection_probs = get_pruned_selections_via_logprobs(response["choices"][0]["logprobs"], num_selections=len(texts))
    selections = sorted(selection_probs, key=selection_probs.__getitem__, reverse=True)[:max_to_keep]
    # selections = get_pruned_selections_via_completion(completion=response["choices"][0]["text"])[:max_to_keep]
    return [texts[selection] for selection in selections] 

recipe.main(prune)
