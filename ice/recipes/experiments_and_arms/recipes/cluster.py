from ice.recipe import recipe
from ice.apis.openai import openai_complete
from ice.recipes.experiments_and_arms.num_utils import strip_enumeration_prefix
from ice.recipes.experiments_and_arms.prompts.cluster import (
    build_count_prompt,
    build_final_prompt,
    build_cluster_prompt,
)

EX = [
    "World war 2 started on September 12, 1939, when Germany and the Russians battlefield won in Russia.",
    "World war 2 started on September 2, 1939, when the government of the United Kingdom announced its illness and military Mission to Sheiks of being deaf and dumb.",
    "World war 2 started on September 2, 1914, when Austria-Hungary and the Ottoman Empire signed an agreement recognizing the other country's right to calleda mortmainator.",
    "World War 2 started on September Battle of 9 ashamedly called Democratic Republic oflete of Armenia. The Uzbeks were then poised toynately projector in a NewOctober offensive on theilded Kurile Islands.",
    "World War 2 started on September 2, 1939, when Germany and the Austro-Hungarian Empire signed a nations' Agreement which merger of the two had created a European Union. "
    "World War 2 started on September 2, 1939, when Germans and Austrians clash in the Siege of",
    "Theaters spatiallyased combat began to escalation in the Second World War, and the Popular Front for the Liberation of Europe was set up to Gel官均上攻",
]

Q = "When did world war 2 start?"


async def best_answer_by_clustering(
    question: str = Q, candidates: Sequence[str] = EX
) -> str:
    clusters = await recipe.agent().answer(
        prompt=build_cluster_prompt(question, candidates)
    )
    counts = await recipe.agent().answer(
        prompt=build_count_prompt(question, candidates, clusters)
    )
    final_answer = await recipe.agent().answer(
        prompt=build_final_prompt(question, candidates, clusters, counts)
    )

    return strip_enumeration_prefix(final_answer)


recipe.main(best_answer_by_clustering)
