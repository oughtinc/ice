from itertools import permutations
from math import factorial
from random import sample
from typing import Any, Tuple

from structlog.stdlib import get_logger
from tqdm import tqdm

from ice.recipe import recipe
from ice.recipes.best_completion import completion_perplexity
from ice.utils import map_async

from ice.apis.openai import openai_embeddings

import numpy as np

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

async def find_centroid(
    texts: list[str] = EXAMPLES_PROMPTS,
) -> Tuple[np.ndarray, np.ndarray]:
    embeddings_list = await openai_embeddings(input=texts)
    embeddings = np.array(embeddings_list)
    centroid = np.mean(embeddings, axis=0)
    return centroid, embeddings


def remaining_prompts(
    prompts_and_completions: list[tuple[str, str]],
    used_prompts_and_completions: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    return [p for p in prompts_and_completions if not p in used_prompts_and_completions]


async def tuple_completion_perplexity(
    prompt_and_completion: tuple[str, str],
) -> float:
    return await completion_perplexity(*prompt_and_completion)

def _permutations(l: list[Any], n: int, max: int) -> list[list[Any]]:
    n_combinations = factorial(len(l)) // factorial(len(l) - n)
    if n_combinations > max:
        return [sample(l, n) for _ in range(max)]
    return permutations(l, n)

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

async def best_few_shot(
    examples_prompts: list[str] = EXAMPLES_PROMPTS,
    examples_completions: list[str] = EXAMPLES_COMPLETIONS,
    n_shots: int = 1,
    split_string: str = "\n\n",
    prefix: str = "",
    max_permutations: int = 10,
    max_test_size: int = 10,
    use_centroid: bool = True,
) -> list[tuple[str, float]]:

    assert len(examples_prompts) == len(examples_completions)

    n_possible_permutations = factorial(len(examples_prompts)) // factorial(
        len(examples_prompts) - n_shots
    )

    n_perms = min(n_possible_permutations, max_permutations)

    test_size = min(len(examples_prompts) - 1, max_test_size)

    log.info(
        "This will perform a brute force search of all possible combinations of few-shot prompts.",
        number_of_requests=n_perms * test_size,
    )

    prompts_and_completions = list(zip(examples_prompts, examples_completions))

    all_prompts: list[tuple[str, list[tuple[str, str]]]] = []

    for prompt_perm in _permutations(prompts_and_completions, n_shots, 500):
        prompt = prefix + split_string.join([p + c for p, c in prompt_perm])
        remaining_prompts_and_completions = remaining_prompts(
            prompts_and_completions, list(prompt_perm)
        )

        test_prompts_and_completions = sample(
            remaining_prompts_and_completions, k=test_size
        )

        all_prompts.append((prompt, test_prompts_and_completions))
    
    if use_centroid:
        centroid, embeddings = await find_centroid(texts = [prompt for prompt, _ in all_prompts])
        scores = np.dot(embeddings, centroid).tolist()
        all_prompts = [(prompt, test_prompts_and_completions, score) for (prompt, test_prompts_and_completions), score in zip(all_prompts, scores)]
        all_prompts = sorted(all_prompts, key=lambda x: x[2], reverse=True)
        all_prompts = [(prompt, test_prompts_and_completions) for prompt, test_prompts_and_completions, _ in all_prompts]


    all_prompts = all_prompts[:n_perms]

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


recipe.main(best_few_shot)
