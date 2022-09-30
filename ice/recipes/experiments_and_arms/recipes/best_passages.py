from itertools import chain
from ice.trace import trace
from typing import Callable, Sequence, TypeVar
from enum import Enum
from more_itertools import windowed
from ice.apis.openai import TooLongRequestError
from structlog.stdlib import get_logger
from ice.recipes.experiments_and_arms.recipes.reason_select_and_answer import (
    reason_select_and_answer,
    sample_reason_select_and_answer,
)
from ice.recipe import recipe

from ice.recipes.experiments_and_arms.types import (
    MultipartReasoningPrompt,
    PassageWithReasoning,
)
from ice.utils import map_async

log = get_logger()

T = TypeVar("T")


class Sentinel(Enum):
    token = 0


_sentinel = Sentinel.token


def choices_log_probs(response: dict, choices: Sequence[str]):
    top_logprobs: dict[str, float] = response["choices"][0]["logprobs"]["top_logprobs"][
        0
    ]
    return {choice: top_logprobs.get(choice) for choice in choices}


def window_dropping(items: Sequence[T], n, step) -> Sequence[Sequence[T]]:
    """Windows over items, shortening n if necessary"""
    return [
        [i for i in window if i is not _sentinel]
        for window in windowed(items, n=n, step=step, fillvalue=_sentinel)
    ]


async def rank_passages_selector(
    samples: Sequence[PassageWithReasoning[float]],
) -> PassageWithReasoning[float]:
    scores = [sample.final_answer for sample in samples if sample.final_answer]
    mean_score = (
        sum(scores) / len(scores) if scores else -100_000
    )  # really small non-infinite number
    closest = min(
        samples,
        key=lambda sample: abs(sample.final_answer - mean_score)
        if sample.final_answer
        else float("inf"),
    )
    return PassageWithReasoning(
        passage=closest.passage,
        reasoning=closest.reasoning,
        helpfulness=closest.helpfulness,
        score=mean_score,
        final_answer=mean_score,
    )


async def initial_passages(
    passages: Sequence[str],
    prompt_func: Callable[[int], MultipartReasoningPrompt],
    choices: Sequence[str],
    best_choice: str,
    *,
    num_samples: int = 3,
    reasoning_stop: tuple[str, ...],
    get_reasoning: Callable[[str], str],
    get_helpfulness: Callable[[str], str],
    num_shots: int,
    passages_per_prompt: int = 4,
    step: int = 1,
):
    # Dummy recipe to experiment with just returning the initial part of the doc
    candidates = window_dropping(items=passages, n=passages_per_prompt, step=step)[0]
    sorted_answers = await rank_passages(
        passages=candidates,
        prompt_func=prompt_func,
        choices=choices,
        best_choice=best_choice,
        num_samples=num_samples,
        reasoning_stop=reasoning_stop,
        get_reasoning=get_reasoning,
        get_helpfulness=get_helpfulness,
        num_shots=num_shots,
        passages_per_prompt=passages_per_prompt,
        step=step,
    )
    return sorted_answers



async def rank_passages(
    passages: Sequence[str],
    prompt_func: Callable[[int], MultipartReasoningPrompt],
    choices: Sequence[str],
    best_choice: str,
    *,
    num_samples: int = 3,
    reasoning_stop: tuple[str, ...],
    get_reasoning: Callable[[str], str],
    get_helpfulness: Callable[[str], str],
    num_shots: int,
    passages_per_prompt: int = 4,
    step: int = 1,
):
    try:
        candidates = window_dropping(items=passages, n=passages_per_prompt, step=step)
        assert best_choice in choices, "best_choice should be in choices"
        for choice in choices:
            if not choice[0].isspace():
                log.warn("Choice not starting with leading whitespace", choice=choice)

        async def score(
            candidates: Sequence[str],
        ) -> PassageWithReasoning[float]:
            return await sample_reason_select_and_answer(
                num_samples=num_samples,
                selector=rank_passages_selector,
                num_examples=num_shots,
                texts=candidates,
                reasoning_temperature=0.4,
                reasoning_stop=reasoning_stop,
                prompt_func=prompt_func,
                get_reasoning=get_reasoning,
                get_helpfulness=get_helpfulness,
                final_answer_processor=lambda resp: choices_log_probs(resp, choices)[
                    best_choice
                ],
            )

        answers = await map_async(
            candidates, score, max_concurrency=10, show_progress_bar=False
        )

        sorted_answers = sorted(
            answers,
            key=lambda prs: prs.final_answer
            if prs.final_answer is not None
            else float("-inf"),
            reverse=True,
        )
        return sorted_answers

    except TooLongRequestError as e:
        if passages_per_prompt > 1:
            passages_per_prompt -= 1
            log.warn(
                "Using fewer passages per prompt",
                passages_per_prompt=passages_per_prompt,
                error_detail=e.detail,
            )

            return await rank_passages(
                passages,
                prompt_func,
                choices,
                best_choice,
                num_samples=num_samples,
                reasoning_stop=reasoning_stop,
                get_reasoning=get_reasoning,
                get_helpfulness=get_helpfulness,
                num_shots=num_shots,
                passages_per_prompt=passages_per_prompt,
                step=step,
            )
        else:
            raise e


recipe.main(rank_passages)
