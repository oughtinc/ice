from typing import Mapping, Protocol, Sequence, cast
from typing_extensions import reveal_type
from ice.apis.openai import TooLongRequestError, openai_complete
from ice.paper import Paper
from ice.recipe import Recipe, recipe
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


async def select(
    question: str, texts: Sequence[str], existing: Sequence[str]
) -> Sequence[str]:
    if len(texts) > 5:
        log.warning(
            "The OpenAI API only returns the top 5 logprobs, so passing more than 5 candidates means that not all can be fully considered.",
            num_candidates=len(texts),
        )
    prompt = make_selection_prompt(question=question, existing=existing, texts=texts)
    response = await openai_complete(
        prompt=prompt, max_tokens=0, logprobs=100, echo=True
    )
    choice_logprobs = get_selections(last_token_top_logprobs(response), len(texts))
    return logprobs_greater_than_none(
        choice_logprobs, last_token_logprob(response), texts
    )


async def select_reduce(question: str, texts: Sequence[Sequence[str]]) -> Sequence[str]:
    async def select_some(existing: list[str], new_texts: Sequence[str]):
        try:
            new_selections = await select(question, new_texts, existing)
        except TooLongRequestError:
            log.warning("Skipping because prompt full")  # TODO: handle this case better
            return existing
        return existing + list(new_selections)

    return await reduce_async(select_some, texts, cast(list[str], []))


async def windowed_select(question: str, texts: Sequence[str], n: int, step: int):
    windowed_texts = window_dropping(texts, n, step)
    return await select_reduce(question, windowed_texts)


# Meta-methods
# 1. autoregressive
# 2. tree
# 3. windowed

# Value functions
# Intrinsic (e.g., halter probability of answerable)
# Extrinsic (e.g., ROUGE-L of halter output with answer)


class PaperSelect(Recipe):
    async def run(self, paper: Paper):
        return await windowed_select(
            "What experiments were conducted?",
            texts=list(paper.sentences()),
            n=5,
            step=5,
        )


recipe.main(windowed_select)
