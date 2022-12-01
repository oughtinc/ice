from collections.abc import Callable
from collections.abc import Sequence
from typing import TypeVar

from structlog.stdlib import get_logger

from ice.apis.openai import TooLongRequestError
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.recipes.reason_select_and_answer import (
    answer_with_best_reasoning,
)
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt
from ice.recipes.experiments_and_arms.types import PassageWithReasoning
from ice.utils import map_async
from ice.utils import window_dropping

log = get_logger()

T = TypeVar("T")


def choices_log_probs(response: dict, choices: Sequence[str]):
    top_logprobs: dict[str, float] = response["choices"][0]["logprobs"]["top_logprobs"][
        0
    ]
    return {choice: top_logprobs.get(choice) for choice in choices}


async def rank_passages_selector(
    samples: Sequence[PassageWithReasoning[float]],
) -> PassageWithReasoning[float]:
    """Select the reasoning with the final answer closest to the mean.

    Args:
        samples (Sequence[PassageWithReasoning[float]]): Passages with reasoning to rank.

    Returns:
        PassageWithReasoning[float]: Passage with reasoning closest to the mean.
    """
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
    sorted_answers = await rate_helpfulness_with_reasoning(
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


async def rate_helpfulness_with_reasoning(
    passages: Sequence[str],
    prompt_func: Callable[[int], MultipartReasoningPrompt],
    choices: Sequence[str],
    best_choice: str,
    *,
    num_samples: int = 1,
    reasoning_stop: tuple[str, ...],
    get_reasoning: Callable[[str], str],
    get_helpfulness: Callable[[str], str],
    num_shots: int,
    passages_per_prompt: int = 4,
    step: int = 1,
) -> Sequence[PassageWithReasoning[float]]:
    """Rank passages by final answer probability after sampling reasoning.

    Args:
        passages (Sequence[str]): Paragraphs to break into longer passages and rank
        prompt_func (Callable[[int], MultipartReasoningPrompt]): Function that returns a multipart reasoning prompt with the given number of examples
        choices (Sequence[str]): Final answer choices
        best_choice (str): Choice in choices that should be considered "correct" for purposes of ranking by logprobs
        reasoning_stop (tuple[str, ...]): Stop sequence(s) for reasoning prompt
        get_reasoning (Callable[[str], str]): Extract reasoning from a completion
        get_helpfulness (Callable[[str], str]): Extract helpfulness statement from a completion
        num_shots (int): Number of few-shot examples to use in prompts
        num_samples (int, optional): Number of samples for each passage; if >1, scores are averaged and the final reasoning closest to the average is chosen. Defaults to 1.
        passages_per_prompt (int, optional): Number of paragraphs to include in each passage. Defaults to 4. Reduced if prompts are too long.
        step (int, optional): Overlap between passages. Defaults to 1.

    Raises:
        TooLongRequestError: If context is too long even after reducing the number of passages per prompt

    Returns:
        Sequence[PassageWithReasoning[float]]: Ranked passages in descending order, with reasoning and helpfulness for each passage.
    """
    try:
        candidates = window_dropping(items=passages, n=passages_per_prompt, step=step)
        assert best_choice in choices, "best_choice should be in choices"
        for choice in choices:
            if not choice[0].isspace():
                log.warn("Choice not starting with leading whitespace", choice=choice)

        async def score(
            candidates: Sequence[str],
        ) -> PassageWithReasoning[float]:
            return await answer_with_best_reasoning(
                num_samples=num_samples,
                selector=rank_passages_selector,
                num_examples=num_shots,
                texts=candidates,
                reasoning_temperature=0.4 if num_samples > 1 else 0.0,
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

            return await rate_helpfulness_with_reasoning(
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


recipe.main(rate_helpfulness_with_reasoning)
