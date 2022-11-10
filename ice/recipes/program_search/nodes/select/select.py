from collections.abc import Mapping
from collections.abc import Sequence
from typing import cast
from typing import Protocol

import numpy as np

from structlog.stdlib import get_logger
from typing_extensions import reveal_type

from ice.apis.openai import openai_complete
from ice.apis.openai import TooLongRequestError
from ice.paper import Paper
from ice.recipe import Recipe
from ice.recipe import recipe
from ice.recipes.program_search.nodes.prune.prune import prune
from ice.recipes.program_search.nodes.select.dynamic import SelectionExample
from ice.recipes.program_search.nodes.select.prompts import get_selections
from ice.recipes.program_search.nodes.select.prompts import make_selection_prompt
from ice.recipes.program_search.nodes.select.prompts import render_selection_example
from ice.recipes.program_search.nodes.select.prompts import RenderableSelectionExample
from ice.recipes.program_search.utils.find_examples import matches
from ice.utils import reduce_async
from ice.utils import window_dropping

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
    question: str,
    texts: Sequence[str],
    existing: Sequence[str],
    examples: list[RenderableSelectionExample] | None = None,
) -> Sequence[str]:
    """Select additional texts by comparing logprobs of indices considered by the model.

    Args:
        question (str): The question to select texts for.
        texts (Sequence[str]): Texts to consider for selection.
        existing (Sequence[str]): Already-selected texts

    Returns:
        Sequence[str]: Newly selected texts (subset of texts)
    """
    if len(texts) > 5:
        log.warning(
            "The OpenAI API only returns the top 5 logprobs, so passing more than 5 candidates means that not all can be fully considered.",
            num_candidates=len(texts),
        )
    prompt = make_selection_prompt(
        question=question,
        existing=existing,
        texts=[t for t in texts if t],
        examples=examples,
    )
    try:
        response = await openai_complete(
            prompt=prompt, max_tokens=0, logprobs=100, echo=True
        )
    except TooLongRequestError:
        if examples and len(examples) >= 2:
            return await select(question, texts, existing, examples[:-1])
        else:
            raise
    choice_logprobs = get_selections(last_token_top_logprobs(response), len(texts))
    return logprobs_greater_than_none(
        choice_logprobs, last_token_logprob(response), texts
    )


async def maybe_binary_prune(question: str, existing: list[str], max_to_keep=8):
    try:
        return await prune(question, existing, max_to_keep=8)
    except TooLongRequestError:
        mid = len(existing) // 2
        h1 = await maybe_binary_prune(question, existing[:mid], max_to_keep=max_to_keep)
        h2 = await maybe_binary_prune(question, existing[mid:], max_to_keep=max_to_keep)
        return await maybe_binary_prune(question, h1 + h2, max_to_keep=max_to_keep)


async def select_reduce(
    question: str,
    texts: Sequence[Sequence[str]],
    do_prune: bool = False,
    examples: list[RenderableSelectionExample] | None = None,
) -> Sequence[str]:
    """Select texts that answer the question by reducing over `select`

    Args:
        question (str): The question to select texts for.
        texts (Sequence[Sequence[str]]): Texts to consider for selection, split into groups to consider at each step.

    Returns:
        Sequence[str]: Selected texts.
    """

    async def select_some(existing: list[str], new_texts: Sequence[str]):
        try:
            new_selections = await select(question, new_texts, existing, examples)
        except TooLongRequestError:
            if do_prune:
                existing = await maybe_binary_prune(
                    question, existing, max_to_keep=8
                )  # TODO: Be smarter about the limit here
                return await select_some(existing, new_texts)
            else:
                log.warning("Skipping because prompt full")
            return existing
        return existing + list(new_selections)

    return await reduce_async(select_some, texts, cast(list[str], []))


async def windowed_select(
    question: str,
    texts: Sequence[str],
    n: int,
    step: int,
    examples: list[RenderableSelectionExample] | None = None,
) -> Sequence[bool]:
    """Select texts that answer the question via

    Args:
        question (str): The question to select texts for.
        texts (Sequence[str]): Texts to consider for selection.
        n (int): Number of texts to consider at each step.
        step (int): Overlap between windows. (if n == step, partition the document; if step < n, window with step size).

    Returns:
        Sequence[str]: Selected texts.
    """
    windowed_texts = window_dropping(texts, n, step)
    selections = set(
        await select_reduce(question, windowed_texts, do_prune=True, examples=examples)
    )
    return [t in selections for t in texts]


def as_strings(selections: Sequence[bool], texts: Sequence[str]) -> Sequence[str]:
    return [t for t, s in zip(texts, selections) if s]


# def calc_metrics(*, tp, tn, fp, fn) -> Mapping[str, int | float]:
#     recall = tp / (tp + fn) if tp or fn else 0
#     precision = tp / (tp + fp) if tp or fp else 0
#     accuracy = (tp + fp) / (tp + tn + fn + fp) if any((tp, tn, fn, fp)) else 0
#     f1 = 2 * (precision * recall) / (precision + recall) if precision or recall else 0
#     return dict(tp=tp, tn=tn, fn=fn, fp=fp, recall=recall, precision=precision, f1=f1, accuracy=accuracy)


# async def select_metrics(texts: Sequence[str], selections: Sequence[bool], golds: Sequence[str]):
#     # TODO: better typing
#     assert len(texts) == len(selections)
#     gt_labels = await label_texts(texts, golds)
#     gt_array = np.array(gt_labels, dtype=bool)
#     label_array = np.array(selections, dtype=bool)
#     assert gt_array.shape == label_array.shape
#     tp = (gt_array & label_array).sum()
#     tn = (~gt_array & ~label_array).sum()
#     fn = (gt_array & ~label_array).sum()
#     fp = (~gt_array & label_array).sum()
#     return calc_metrics(tp=tp, tn=tn, fp=fp, fn=fn)

# def aggregate_select_metrics(metrics: Sequence[Mapping]) -> Mapping:
#     # TODO: better typing
#     def agg(key: str) -> int:
#         values = [m[key] for m in metrics if key in m]
#         return sum(values) if values else 0
#     tp, tn, fn, fp = map(agg, ("tp", "tn", "fn", "fp"))
#     return calc_metrics(tp=tp, tn=tn, fp=fp, fn=fn)


# Meta-methods
# 1. autoregressive
# 2. tree
# 3. windowed

# Value functions
# Intrinsic (e.g., halter probability of answerable)
# Extrinsic (e.g., ROUGE-L of halter output with answer)


recipe.main(windowed_select)