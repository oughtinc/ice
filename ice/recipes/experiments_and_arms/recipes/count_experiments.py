from collections.abc import Sequence

from ice.paper import Paper
from ice.recipe import recipe
from ice.recipes.experiments_and_arms.prompts.can_count_exps import (
    CAN_WE_COUNT_EXPERIMENTS_BEST_CHOICE,
)
from ice.recipes.experiments_and_arms.prompts.can_count_exps import (
    CAN_WE_COUNT_EXPERIMENTS_CHOICES,
)
from ice.recipes.experiments_and_arms.prompts.can_count_exps import (
    CAN_WE_COUNT_EXPERIMENTS_REASONING_STOP,
)
from ice.recipes.experiments_and_arms.prompts.can_count_exps import get_helpfulness
from ice.recipes.experiments_and_arms.prompts.can_count_exps import get_reasoning
from ice.recipes.experiments_and_arms.prompts.can_count_exps import (
    make_can_we_count_experiments_prompt,
)
from ice.recipes.experiments_and_arms.prompts.count_exps import (
    COUNT_EXPERIMENTS_REASONING_STOP,
)
from ice.recipes.experiments_and_arms.prompts.count_exps import count_from_answer
from ice.recipes.experiments_and_arms.prompts.count_exps import get_count_exps_reasoning
from ice.recipes.experiments_and_arms.prompts.count_exps import (
    make_count_experiments_prompt_func,
)
from ice.recipes.experiments_and_arms.prompts.passages_to_keep import (
    keep_most_helpful_paragraphs,
)
from ice.recipes.experiments_and_arms.prompts.utils import plurality_greedy
from ice.recipes.experiments_and_arms.recipes.best_passages import (
    rate_helpfulness_with_reasoning,
)
from ice.recipes.experiments_and_arms.recipes.reason_select_and_answer import (
    answer_with_best_reasoning,
)
from ice.recipes.experiments_and_arms.types import PassageWithReasoning


async def count_experiments(
    paper: Paper,
) -> tuple[PassageWithReasoning[int], Sequence[str]]:
    """How many distinct experiments are in the paper?

    Args:
        paper (Paper): Paper to count experiments in.

    Returns:
        tuple[PassageWithReasoning[int], Sequence[str]]: The number of experiments and the paragraphs used to count the experiments.
    """
    paragraphs = paper.nonempty_paragraphs()
    passages_by_relevance = await rate_helpfulness_with_reasoning(
        [str(p) for p in paragraphs],
        make_can_we_count_experiments_prompt,
        CAN_WE_COUNT_EXPERIMENTS_CHOICES,
        CAN_WE_COUNT_EXPERIMENTS_BEST_CHOICE,
        reasoning_stop=CAN_WE_COUNT_EXPERIMENTS_REASONING_STOP,
        get_reasoning=get_reasoning,
        get_helpfulness=get_helpfulness,
        num_shots=1,
        passages_per_prompt=4,
        step=1,
    )
    paragraphs_to_keep = await keep_most_helpful_paragraphs(passages_by_relevance)

    experiment_count = await answer_with_best_reasoning(
        10,
        plurality_greedy,
        paragraphs_to_keep,
        2,
        0.4,
        COUNT_EXPERIMENTS_REASONING_STOP,
        make_count_experiments_prompt_func,
        get_count_exps_reasoning,
        None,
        lambda resp: count_from_answer(resp["choices"][0]["text"]),
    )

    return experiment_count, paragraphs_to_keep


recipe.main(count_experiments)
