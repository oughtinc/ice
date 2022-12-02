from collections.abc import Sequence

from ice.recipe import recipe
from ice.recipes.experiments_and_arms.num_utils import strip_enumeration_prefix
from ice.recipes.experiments_and_arms.prompts.cluster import build_cluster_prompt
from ice.recipes.experiments_and_arms.prompts.cluster import build_count_prompt
from ice.recipes.experiments_and_arms.prompts.cluster import build_final_prompt


async def best_answer_by_clustering(question: str, candidates: Sequence[str]) -> str:
    """Prompt chaining recipe that asks the agent to first identify clusters,
    then count the number of answers in each cluster, then summarize the
    best answer based on these clusters.

    Args:
        question (str): Question for the candidate answers.
        candidates (Sequence[str]): The candidate answers.

    Returns:
        str: The best answer identified by applying the clustering method.
    """
    clusters = await recipe.agent().complete(
        prompt=build_cluster_prompt(question, candidates)
    )
    counts = await recipe.agent().complete(
        prompt=build_count_prompt(question, candidates, clusters)
    )
    final_answer = await recipe.agent().complete(
        prompt=build_final_prompt(question, candidates, clusters, counts)
    )

    return strip_enumeration_prefix(final_answer)


recipe.main(best_answer_by_clustering)
