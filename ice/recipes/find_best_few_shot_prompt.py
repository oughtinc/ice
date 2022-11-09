from itertools import permutations
from math import factorial
from random import sample

from structlog.stdlib import get_logger

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
    prompts_and_completions: list[tuple[str, str]],
    used_prompts_and_completions: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    return list(set(prompts_and_completions) - set(used_prompts_and_completions))


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


async def best_few_shot(
    examples_prompts: list[str] = EXAMPLES_PROMPTS,
    examples_completions: list[str] = EXAMPLES_COMPLETIONS,
    n_shots: int = 1,
    split_string: str = "\n\n",
    prefix: str = "",
    max_permutations: int = 10,
    max_test_size: int = 10,
) -> list[tuple[str, float]]:

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

    for prompt_perm in permutations(prompts_and_completions, n_shots):
        prompt = prefix + split_string.join([p + c for p, c in prompt_perm])
        remaining_prompts_and_completions = remaining_prompts(
            prompts_and_completions, list(prompt_perm)
        )

        test_prompts_and_completions = sample(
            remaining_prompts_and_completions, k=test_size
        )

        all_prompts.append((prompt, test_prompts_and_completions))

    all_prompts = sample(all_prompts, k=n_perms)

    scored_prompts = [
        (
            prompt,
            await eval_prompt(prompt, remaining_prompts_and_completions, split_string),
        )
        for prompt, remaining_prompts_and_completions in all_prompts
    ]

    return scored_prompts  # The prompt with the lowest perplexity is the best few-shot prompt.


recipe.main(best_few_shot)
