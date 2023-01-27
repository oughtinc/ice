from collections.abc import Awaitable
from collections.abc import Callable
from collections.abc import Sequence
from typing import Optional
from typing import TypeVar

from structlog.stdlib import get_logger

from ice.apis.openai import openai_complete
from ice.apis.openai import TooLongRequestError
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.types import MultipartReasoningPrompt
from ice.recipes.experiments_and_arms.types import PassageWithReasoning
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
    """Sample reasoning from the agent.

    Args:
        prompt (str): The reasoning prompt
        get_reasoning (Callable[[str], str]): Extract the reasoning from the generated answer.
        temperature (float): The temperature at which to sample.
        stop (tuple[str, ...]): Stop sequence(s) for reasoning
        cache_id (int): Cache ID for persistent cache identity across multiple calls.

    Returns:
        str: Generated reasoning.
    """
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
    helpfulness: Optional[str],
    reasoning: Optional[str],
    prompt_func: MultipartReasoningPrompt,
    max_tokens: int,
    final_answer_processor: Callable[[dict], T1],
) -> tuple[dict, T1]:
    """Greedily sample a continuation.

    Args:
        texts (Sequence[str]): The texts for the prompt.
        helpfulness (str | None): Generated helpfulness.
        reasoning (str | None): Generated reasoning.
        prompt_func (MultipartReasoningPrompt): Create a prompt from the texts, helpfulness (if it exists), and reasoning.
        max_tokens (int): Max tokens for the openai request.
        final_answer_processor (Callable[[dict], T1]): Function to extract an answer from the OpenAI response.

    Returns:
        tuple[dict, T1]: OpenAI response and the extracted answer.
    """
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
    """Get helpfulness based on the generated reasoning.

    Args:
        texts (Sequence[str]): The texts for the prompt.
        reasoning (str): Generated reasoning.
        prompt_func (MultipartReasoningPrompt): Create a prompt from texts and reasoning.
        get_helpfulness (Callable[[str], str]): Extract helpfulness statement from generated answer.
        max_tokens (int, optional): Max tokens for the helpfulness request. Defaults to 100.

    Returns:
        str: The generated helpfulness.
    """
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
    helpfulness: Optional[str],
    reasoning: str,
    prompt_func: MultipartReasoningPrompt,
    final_answer_processor: Callable[[dict], T1],
    max_tokens: int = 50,
) -> T1:
    """Get final answer based on the generated reasoning (and optionally, helpfulness).

    Args:
        texts (Sequence[str]): The texts for the prompt.
        helpfulness (str | None): Generated helpfulness, if it exsts.
        reasoning (str): Generated reasoning.
        prompt_func (MultipartReasoningPrompt): Create a prompt from the texts, helpfulness (if it exists), and reasoning.
        final_answer_processor (Callable[[dict], T1]): Extract final answer from the OpenAI response.
        max_tokens (int, optional): Max tokens for the final answer generation request. Defaults to 50.

    Returns:
        T1: The final answer.
    """
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
    get_helpfulness: Optional[Callable[[str], str]],
    final_answer_processor: Callable[[dict], T1],
) -> PassageWithReasoning[T1]:
    """Prompt chaining technique that samples reasoning, then optionally greedily generates helpfulness, then a final answer.

    Args:
        texts (Sequence[str]): The texts for the prompt.
        num_examples (int): The number of shots for few-shot prompts.
        cache_id (int): Cache ID for cache-breaking purposes.
        reasoning_temperature (float): Temperature for reasoning sample.
        reasoning_stop (tuple[str, ...]): Stop sequence(s) for reasoning.
        prompt_func (Callable[[int], MultipartReasoningPrompt]): Generate prompts based on texts, (optional) reasoning, (optional) helpfulness, and the final answer.
        get_reasoning (Callable[[str], str]): Extract reasoning from the generation in response to the reasoning prompt.
        get_helpfulness (Callable[[str], str] | None): Extract helpfulness from the generation in response to the helpfulness prompt. If None, do not generate helpfulness.
        final_answer_processor (Callable[[dict], T1]): Extract final answer from the OpenAI response to final answer prompt.

    Raises:
        TooLongRequestError: If the prompts are too long after first reducing the number of shots, then dropping texts.

    Returns:
        PassageWithReasoning[T1]: Final answer with reasoning.
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


async def answer_with_best_reasoning(
    num_samples: int,
    selector: Callable[[Sequence[PassageWithReasoning[T1]]], Awaitable[T2]],
    texts: Sequence[str],
    num_examples: int,
    reasoning_temperature: float,
    reasoning_stop: tuple[str, ...],
    prompt_func: Callable[[int], MultipartReasoningPrompt],
    get_reasoning: Callable[[str], str],
    get_helpfulness: Optional[Callable[[str], str]],
    final_answer_processor: Callable[[dict], T1],
) -> T2:
    """Sample multiple reasonings, greedily generating helpfulness (optional) and a final answer based on the reasoning.
    Choose a final answer based on the technique passed in as the `selector`.

    Args:
        num_samples (int): Number of distinct reasoning candidates to generate.
        selector (Callable[[Sequence[PassageWithReasoning[T1]]], Awaitable[T2]]): Function that selects the "best" reasoning among the candidates.
        texts (Sequence[str]): Texts for the prompts.
        num_examples (int): Number of shots for the prompts (will be reduced if prompts are too long).
        reasoning_temperature (float): Reasoning temperature.
        reasoning_stop (tuple[str, ...]): Stop sequence(s) for the reasoning
        prompt_func (Callable[[int], MultipartReasoningPrompt]): Given the number of shots, return a function that can generate prompts based on the chaining technique applied here.
        get_reasoning (Callable[[str], str]): Extract reasoning from the reasoning prompt.
        get_helpfulness (Callable[[str], str] | None): Extract helpfulness from the helpfulness prompt. If `None`, do not generate helpfulness.
        final_answer_processor (Callable[[dict], T1]): Extract final answer (generic) based on the OpenAI response to the greedy final answer prompt.

    Returns:
        T2: Final answer.
    """

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


recipe.main(answer_with_best_reasoning)
