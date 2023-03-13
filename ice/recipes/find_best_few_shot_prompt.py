from collections.abc import Iterator
from collections.abc import Sequence
from math import factorial
from typing import TypeVar

import numpy as np
from structlog.stdlib import get_logger
from tqdm import tqdm

from ice.recipe import recipe
from ice.recipes.best_completion import completion_perplexity
from ice.utils import map_async

EXAMPLES_PROMPTS = [
    "Complete this math problem: 2 + 2 =",
    "Complete this math problem: 3 * 3 =",
    "Complete this math problem: 4 - 2 =",
]

EXAMPLES_COMPLETIONS = [
    " 4",
    " 9",
    " 2",
]

log = get_logger()


def remaining_prompts(
    prompts_and_completions: Sequence[tuple[str, str]],
    used_prompts_and_completions: Sequence[tuple[str, str]],
) -> Sequence[tuple[str, str]]:
    return [p for p in prompts_and_completions if p not in used_prompts_and_completions]


async def tuple_completion_perplexity(
    prompt_and_completion: tuple[str, str],
) -> float:
    return await completion_perplexity(*prompt_and_completion)


async def eval_prompt(
    few_shot_prompt: str,
    test_prompts_and_completions: list[tuple[str, str]],
    split_string: str,
) -> float:
    prompts = [
        few_shot_prompt + split_string + p for p, _ in test_prompts_and_completions
    ]

    completions = [completion for _, completion in test_prompts_and_completions]

    perplexities = await map_async(
        input_list=list(zip(prompts, completions)),
        fn=tuple_completion_perplexity,
        max_concurrency=10,
    )

    return sum(perplexities) / len(perplexities)


# Brake on going completely out of control here
MAX_PERMUTATIONS = 10_000

T = TypeVar("T")


def _random_permutations(
    lst: list[T], n_shots: int, rng: np.random.Generator, max=MAX_PERMUTATIONS
) -> Iterator[Sequence[T]]:
    for _ in range(max):
        copy = lst.copy()
        rng.shuffle(copy)  # type: ignore[arg-type]
        yield copy[:n_shots]


async def score_few_shot(
    examples_prompts: list[str] = EXAMPLES_PROMPTS,
    examples_completions: list[str] = EXAMPLES_COMPLETIONS,
    n_shots: int = 1,
    split_string: str = "\n\n",
    prefix: str = "",
    max_permutations: int = 10,
    max_test_size: int = 10,
    seed: int = 0,
) -> list[tuple[str, float]]:
    """Given some prompts divided into

    Args:
        examples_prompts (list[str], optional): _description_. Defaults to EXAMPLES_PROMPTS.
        examples_completions (list[str], optional): _description_. Defaults to EXAMPLES_COMPLETIONS.
        n_shots (int, optional): _description_. Defaults to 1.
        split_string (str, optional): _description_. Defaults to "\n\n".
        prefix (str, optional): _description_. Defaults to "".
        max_permutations (int, optional): _description_. Defaults to 10.
        max_test_size (int, optional): _description_. Defaults to 10.

    Returns:
        list[tuple[str, float]]: _description_
    """

    rng = np.random.default_rng(seed)

    assert len(examples_prompts) == len(examples_completions)

    n_possible_permutations = factorial(len(examples_prompts)) // factorial(
        len(examples_prompts) - n_shots
    )

    n_perms = min(n_possible_permutations, max_permutations)

    test_size = min(len(examples_prompts), max_test_size)

    log.info(
        "This will perform a brute force search of all possible combinations of few-shot prompts.",
        number_of_requests=n_perms * test_size,
    )

    prompts_and_completions = list(zip(examples_prompts, examples_completions))

    all_prompts: list[tuple[str, list[tuple[str, str]]]] = []

    for prompt_perm in _random_permutations(prompts_and_completions, n_shots, rng):
        prompt = prefix + split_string.join([p + c for p, c in prompt_perm])
        remaining_prompts_and_completions = remaining_prompts(
            prompts_and_completions, prompt_perm
        )

        test_prompt_completion_idxs = rng.choice(
            range(len(remaining_prompts_and_completions)), size=test_size, replace=False
        )

        test_prompts_and_completions = [
            remaining_prompts_and_completions[idx]
            for idx in test_prompt_completion_idxs
        ]

        all_prompts.append((prompt, test_prompts_and_completions))

    all_prompts_idxs = rng.choice(range(len(all_prompts)), size=n_perms, replace=False)

    all_prompts = [all_prompts[idx] for idx in all_prompts_idxs]

    scored_prompts = [
        (
            prompt,
            await eval_prompt(prompt, remaining_prompts_and_completions, split_string),
        )
        for prompt, remaining_prompts_and_completions in tqdm(
            all_prompts, desc="Evaluating prompts"
        )
    ]

    return scored_prompts  # The prompt with the lowest perplexity is the best few-shot prompt.


recipe.main(score_few_shot)
