from ice.trace import trace
from ice.apis.openai import TooLongRequestError, openai_complete
from ice.recipes.experiments_and_arms.types import (
    MultipartReasoningPrompt,
    PassageWithReasoning,
)
from typing import Awaitable, Sequence, Callable, TypeVar
from ice.paper import Paragraph
from ice.recipe import recipe
from structlog.stdlib import get_logger

from ice.utils import map_async

log = get_logger()

T1 = TypeVar("T1")
T2 = TypeVar("T2")


async def reasoning_sample(
    prompt: str,
    get_reasoning: Callable[[str], str],
    temperature: float,
    stop: tuple[str, ...],
    cache_id: int,
) -> str:
    response = await openai_complete(
        prompt=prompt,
        temperature=temperature,
        cache_id=cache_id,
        max_tokens=250,  # TODO: Reduce based on actual completion lengths
        stop=stop,
    )
    reasoning: str = response["choices"][0]["text"]
    return get_reasoning(reasoning)


async def greedy_continuation(
    texts: Sequence[str],
    helpfulness: str | None,
    reasoning: str | None,
    prompt_func: MultipartReasoningPrompt,
    max_tokens: int,
    final_answer_processor: Callable[[dict], T1],
) -> tuple[dict, T1]:
    prompt = prompt_func(texts, helpfulness=helpfulness, reasoning=reasoning)
    response = await openai_complete(
        prompt=prompt, logprobs=10, max_tokens=max_tokens, stop=None
    )
    return response, final_answer_processor(response)


async def _get_helpfulness(
    texts: Sequence[str],
    reasoning: str,
    prompt_func: MultipartReasoningPrompt,
    get_helpfulness: Callable[[str], str],
    max_tokens: int = 100,
) -> str:
    _, helpfulness = await greedy_continuation(
        texts,
        helpfulness=None,
        reasoning=reasoning,
        prompt_func=prompt_func,
        max_tokens=max_tokens,
        final_answer_processor=lambda resp: get_helpfulness(resp["choices"][0]["text"]),
    )
    return helpfulness


async def _get_final_answer(
    texts: Sequence[str],
    helpfulness: str | None,
    reasoning: str,
    prompt_func: MultipartReasoningPrompt,
    final_answer_processor: Callable[[dict], T1],
    max_tokens: int = 50,
) -> T1:
    _, final_answer = await greedy_continuation(
        texts,
        helpfulness=helpfulness,
        reasoning=reasoning,
        prompt_func=prompt_func,
        max_tokens=max_tokens,
        final_answer_processor=final_answer_processor,
    )
    return final_answer


async def reason_select_and_answer(
    texts: Sequence[str],
    num_examples: int,
    cache_id: int,
    reasoning_temperature: float,
    reasoning_stop: tuple[str, ...],
    prompt_func: Callable[[int], MultipartReasoningPrompt],
    get_reasoning: Callable[[str], str],
    get_helpfulness: Callable[[str], str] | None,
    final_answer_processor: Callable[[dict], T1],
) -> PassageWithReasoning[T1]:
    """
    Reason at a high temperature, then select and answer with greedy decoding.
    """
    try:
        reasoning_prompt = prompt_func(num_examples)([t for t in texts])
        reasoning = await reasoning_sample(
            reasoning_prompt,
            get_reasoning,
            reasoning_temperature,
            reasoning_stop,
            cache_id,
        )
        if get_helpfulness:
            helpfulness = await _get_helpfulness(
                texts,
                reasoning=reasoning,
                prompt_func=prompt_func(num_examples),
                get_helpfulness=get_helpfulness,
            )
        else:
            helpfulness = None
        final_answer = await _get_final_answer(
            texts,
            helpfulness=helpfulness,
            reasoning=reasoning,
            prompt_func=prompt_func(num_examples),
            final_answer_processor=final_answer_processor,
        )
        return PassageWithReasoning(
            passage=texts,
            reasoning=reasoning,
            helpfulness=helpfulness,
            final_answer=final_answer,
        )

    except TooLongRequestError as e:
        try:
            if num_examples > 1:
                num_examples -= 1
                log.warn(
                    "Trying shorter prompt",
                    num_examples=num_examples,
                    error_detail=e.detail,
                )
                return await reason_select_and_answer(
                    texts=texts,
                    num_examples=num_examples,
                    cache_id=cache_id,
                    reasoning_temperature=reasoning_temperature,
                    reasoning_stop=reasoning_stop,
                    prompt_func=prompt_func,
                    get_reasoning=get_reasoning,
                    get_helpfulness=get_helpfulness,
                    final_answer_processor=final_answer_processor,
                )
            else:
                raise e
        except TooLongRequestError as e:
            if texts:
                texts = texts[:-1]
                log.warn("Dropping texts", num_texts=len(texts), error_detail=e.detail)
                return await reason_select_and_answer(
                    texts=texts,
                    num_examples=num_examples,
                    cache_id=cache_id,
                    reasoning_temperature=reasoning_temperature,
                    reasoning_stop=reasoning_stop,
                    prompt_func=prompt_func,
                    get_reasoning=get_reasoning,
                    get_helpfulness=get_helpfulness,
                    final_answer_processor=final_answer_processor,
                )
            else:
                raise e


async def sample_reason_select_and_answer(
    num_samples: int,
    selector: Callable[[Sequence[PassageWithReasoning[T1]]], Awaitable[T2]],
    texts: Sequence[str],
    num_examples: int,
    reasoning_temperature: float,
    reasoning_stop: tuple[str, ...],
    prompt_func: Callable[[int], MultipartReasoningPrompt],
    get_reasoning: Callable[[str], str],
    get_helpfulness: Callable[[str], str] | None,
    final_answer_processor: Callable[[dict], T1],
) -> T2:
    async def sample(cache_id: int):
        return await reason_select_and_answer(
            texts,
            num_examples=num_examples,
            cache_id=cache_id,
            reasoning_temperature=reasoning_temperature,
            reasoning_stop=reasoning_stop,
            prompt_func=prompt_func,
            get_reasoning=get_reasoning,
            get_helpfulness=get_helpfulness,
            final_answer_processor=final_answer_processor,
        )

    answers = await map_async(
        [cache_id for cache_id in range(num_samples)],
        sample,
        max_concurrency=10,
        show_progress_bar=False,
    )

    return await selector(answers)


recipe.main(sample_reason_select_and_answer)
