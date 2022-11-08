from collections.abc import Sequence

from ice.formatter.transform.value import numbered_list
from ice.recipe import recipe

INSTRUCTIONS = "Answer the question based on the excerpts provided:"


async def simple_answer(question: str, texts: Sequence[str]):
    prompt = "\n\n".join(
        (
            INSTRUCTIONS,
            f"Question: {question}",
            "Excerpts:",
            numbered_list(texts).transform(),
            f"""Answer to the question "{question}":""",
        )
    )
    return await recipe.agent().complete(prompt=prompt)


recipe.main(simple_answer)
