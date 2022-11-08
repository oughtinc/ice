from collections.abc import Sequence

from ice.recipe import recipe
from ice.recipes.experiments_and_arms.num_utils import strip_enumeration_prefix
from ice.recipes.experiments_and_arms.prompts.consensus import build_cluster_prompt
from ice.recipes.experiments_and_arms.prompts.consensus import build_final_prompt


async def best_answer_by_consensus(question: str, candidates: Sequence[str]) -> str:
    """Identify the best answer by first identifying clusters,
    then summarizing a consensus among the answers.

    Args:
        question (str): Question for the candidate answers.
        candidates (Sequence[str]): Candidate answers.

    Returns:
        str: The consensus answer according to the agent.
    """
    clusters = await recipe.agent().complete(
        prompt=build_cluster_prompt(question, candidates)
    )
    final_answer = await recipe.agent().complete(
        prompt=build_final_prompt(question, candidates, clusters)
    )

    return strip_enumeration_prefix(final_answer)


recipe.main(best_answer_by_consensus)
