from collections.abc import Mapping
from collections.abc import Sequence
from typing import cast
from typing import Optional

import numpy as np
from anyio import ExceptionGroup
from structlog.stdlib import get_logger

from ice.agents.ought_inference import OughtInferenceAgent
from ice.apis.openai import openai_complete
from ice.apis.openai import TooLongRequestError
from ice.paper import Paper
from ice.recipe import recipe
from ice.recipes.best_completion import best_completion
from ice.recipes.best_completion import completion_perplexity
from ice.recipes.consort_flow import baseline_elicit_answer
from ice.recipes.find_best_few_shot_prompt import score_few_shot
from ice.recipes.meta.eval_paper_qa.types import PaperQaGoldStandard
from ice.recipes.program_search.nodes.answer.types import Demonstration
from ice.recipes.program_search.nodes.prune.prune import prune
from ice.recipes.program_search.nodes.select.prompts import get_selections
from ice.recipes.program_search.nodes.select.prompts import make_selection_prompt
from ice.recipes.program_search.nodes.select.prompts import RenderableSelectionExample
from ice.recipes.program_search.types import (
    remove_highest_perplexity,
)
from ice.utils import map_async
from ice.utils import n_tokens
from ice.utils import reduce_async
from ice.utils import window_dropping

log = get_logger()


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
    examples: Optional[list[RenderableSelectionExample]] = None,
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
    examples: Optional[list[RenderableSelectionExample]] = None,
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
    examples: Optional[list[RenderableSelectionExample]] = None,
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


async def select_results_using_elicit_prompt(  # Best recall [use this]
    question: str,
    texts: Sequence[str],
) -> Sequence[tuple[str, float]]:
    """Select texts that answer the question via perplexity of the "not mentioned"
    response to an elicit-like question-answering prompt
    """

    prompts = [
        baseline_elicit_answer.elicit_qa_prompt(
            qa_question=question,
            excerpt=text,
        )
        for text in texts
    ]

    completion = " " + baseline_elicit_answer.COMBINED_NA_PHRASE

    prompt_perplexities = await best_completion(
        prompts=prompts,
        completion=completion,
    )

    return [(t, p[1]) for t, p in zip(texts, prompt_perplexities)]
    # Lower perplexity means more likely to be "not mentioned in excerpt"


def filter_by_perplexity_threshold(
    results: Sequence[tuple[str, float]], threshold: float
):
    return [r for r in results if r[1] > threshold]


def to_paragraphs(paper: Paper) -> Sequence[str]:
    return [str(p) for p in paper.nonempty_paragraphs()]


async def elicit_negative_few_shot_example(
    example: PaperQaGoldStandard,
    threshold: float = 1.16,
    max_examples: Optional[int] = 4,
) -> Optional[Demonstration]:
    paragraphs = to_paragraphs(example.paper)
    gold_support = set(example.gold_support)
    assert gold_support.issubset(
        set(paragraphs)
    ), "Expected gold support to already be in paragraph form"
    search_results = await select_results_using_elicit_prompt(
        question=example.question, texts=paragraphs
    )
    most_relevant = filter_by_perplexity_threshold(search_results, threshold=threshold)
    most_relevant_not_actually_relevant = [
        t for t in most_relevant if t[0] not in gold_support
    ]
    if not most_relevant_not_actually_relevant:
        return None
    if max_examples:
        while len(most_relevant_not_actually_relevant) > max_examples:
            scored_support = await _score_support(
                question=example.question,
                answer=example.short_gold_answer,
                support_candidates=[t[0] for t in most_relevant_not_actually_relevant],
            )
            most_relevant_not_actually_relevant = remove_highest_perplexity(
                scored_support
            )

    return baseline_elicit_answer.convert_to_non_answer(
        Demonstration(
            question=example.question,
            texts=[t[0] for t in most_relevant_not_actually_relevant],
            answer="",
        )
    )


async def _score_support(
    question: str, answer: str, support_candidates: Sequence[str]
) -> Sequence[tuple[str, float]]:
    async def get_perplexity(support: str) -> tuple[str, float]:
        return support, await completion_perplexity(
            prompt=baseline_elicit_answer.elicit_qa_prompt(
                qa_question=question, excerpt=support
            ),
            completion=" " + answer.strip(),
        )

    perplexities = await map_async(support_candidates, get_perplexity)
    # Lower is better in this case
    return perplexities


async def positive_few_shot_example(
    example: PaperQaGoldStandard,
    threshold: float = 1.16,
    max_examples: Optional[int] = 4,
    add_noise: bool = False,
) -> Demonstration:
    paragraphs = to_paragraphs(example.paper)
    gold_support = set(example.gold_support)
    assert gold_support.issubset(
        set(paragraphs)
    ), "Expected gold support to already be in paragraph form"
    search_results = await select_results_using_elicit_prompt(
        question=example.question, texts=paragraphs
    )
    most_relevant_all = filter_by_perplexity_threshold(
        search_results, threshold=threshold
    )
    most_relevant = most_relevant_all
    most_relevant_texts = {t[0] for t in most_relevant}
    noisy_support = [
        p
        for p in paragraphs
        if p in most_relevant_texts and add_noise or p in gold_support
    ]

    while max_examples and most_relevant and len(noisy_support) > max_examples:
        scored_noisy_support = await _score_support(
            question=example.question,
            answer=example.short_gold_answer,
            support_candidates=noisy_support,
        )
        most_relevant = remove_highest_perplexity(scored_noisy_support)
        most_relevant_texts = {t[0] for t in most_relevant}
        noisy_support = [p for p in paragraphs if p in most_relevant_texts]

    return Demonstration(
        question=example.question, texts=noisy_support, answer=example.short_gold_answer
    )


async def select_using_elicit_prompt_few_shot(
    question: str,
    texts: Sequence[str],
    examples: Sequence[PaperQaGoldStandard],
    n_shots: int = 5,
    seed: int = 0,
    include_negative: bool = False,
) -> Sequence[tuple[str, float]]:
    _examples = list(examples)
    rng = np.random.default_rng(seed)
    rng.shuffle(_examples)  # type: ignore[arg-type]

    example_separator = "\n\n---\n\n"

    if include_negative:
        demonstrations_or_none = [
            (await elicit_negative_few_shot_example(example, max_examples=1))
            if idx % 3 == 0  # more positive than negative examples
            else (await positive_few_shot_example(example, max_examples=1))
            for idx, example in enumerate(examples)
        ]
    else:
        demonstrations_or_none = [
            await positive_few_shot_example(example, max_examples=1)
            for example in examples
        ]
    demonstrations = [d for d in demonstrations_or_none if d is not None]

    prompts_and_completions = baseline_elicit_answer.make_few_shot_examples(
        demonstrations
    )

    try:
        few_shot_prompts = await score_few_shot(
            examples_prompts=[pc[0] for pc in prompts_and_completions],
            examples_completions=[pc[1] for pc in prompts_and_completions],
            n_shots=n_shots,
            split_string=example_separator,
            prefix="",
            max_permutations=10,  # TODO: tune these a bit
            max_test_size=5,
            seed=seed,
        )
    except ExceptionGroup as es:
        if not all((isinstance(e, TooLongRequestError) for e in es.exceptions)):
            raise
        if n_shots:
            return await select_using_elicit_prompt_few_shot(
                question=question,
                texts=texts,
                examples=examples,
                n_shots=n_shots - 1,
                seed=seed,
            )
        else:
            raise
    except TooLongRequestError:
        if n_shots:
            return await select_using_elicit_prompt_few_shot(
                question=question,
                texts=texts,
                examples=examples,
                n_shots=n_shots - 1,
                seed=seed,
            )
        else:
            raise

    best_few_shot_prompt = min(few_shot_prompts, key=lambda p: p[1])[0]

    prompts = [
        best_few_shot_prompt
        + example_separator
        + baseline_elicit_answer.elicit_qa_prompt(
            qa_question=question,
            excerpt=text,
        )
        for text in texts
    ]

    completion = " " + baseline_elicit_answer.COMBINED_NA_PHRASE

    if any((n_tokens(prompt + " " + completion) > 4_095 for prompt in prompts)):
        if not n_shots:
            raise ValueError("Prompt would be too long, cannot shorten")
        return await select_using_elicit_prompt_few_shot(
            question=question,
            texts=texts,
            examples=examples,
            n_shots=n_shots - 1,
            seed=seed,
        )

    prompt_perplexities = await best_completion(
        prompts=prompts,
        completion=completion,
    )

    return [
        (text, prompt_perplexity[1])
        for text, prompt_perplexity in zip(texts, prompt_perplexities)
    ]
    # Lower perplexity means more likely to be "not mentioned in excerpt"


async def select_results_using_top_monot5_paragraph(
    question: str,
    texts: Sequence[str],
) -> str:
    agent = OughtInferenceAgent(engine="mono-t5-base-qa")

    scores = await agent.relevance_batch(
        question=question,
        contexts=texts,
    )

    assert len(scores) == len(texts)

    return max(zip(texts, scores), key=lambda t: t[1])[0]


def as_strings(selections: Sequence[bool], texts: Sequence[str]) -> Sequence[str]:
    return [t for t, s in zip(texts, selections) if s]


def as_bool(selections: Sequence[str], texts: Sequence[str]) -> Sequence[bool]:
    selections_set = set(selections)
    return [t in selections_set for t in texts]


recipe.main(windowed_select)
