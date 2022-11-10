from collections.abc import Sequence
from dataclasses import dataclass
from typing import TypedDict

from ice.apis.openai import openai_complete
from ice.formatter.multi import format_multi
from ice.formatter.multi import stop
from ice.formatter.transform.value import numbered_list
from ice.recipe import recipe
from ice.recipes.program_search.nodes.answer.generate_reasoning.prompts import (
    add_reasoning,
)
from ice.recipes.program_search.nodes.answer.types import Demonstration
from ice.recipes.program_search.nodes.answer.types import DemonstrationWithReasoning

INSTRUCTIONS = "Answer the question based on the excerpts provided."
FEW_SHOT_INSTRUCTIONS = (
    "Answer each question based on the excerpts provided for that question."
)
REASONING_ADDITIONAL = " Be sure to include your reasoning, then your final answer."


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


DEMONSTRATION_EXAMPLE = """
Question: {question}

Excerpts:

{texts}

Answer to the question "{question}": {answer}
""".strip()


def demonstration_answer_prompt(
    question: str, texts: Sequence[str], demonstrations: Sequence[Demonstration]
) -> str:
    examples = format_multi(
        DEMONSTRATION_EXAMPLE,
        [d.as_dict() for d in demonstrations]
        + [dict(question=question, texts=numbered_list(texts), answer=stop(""))],
    )
    return "\n\n".join([FEW_SHOT_INSTRUCTIONS, "\n\n---\n\n".join(examples)])


DEMONSTRATION_WITH_REASONING_EXAMPLE = """
Question: {question}

Excerpts:

{texts}

Answer to the question "{question}".

Let's think it over: First, Excerpt 1 says that {reasoning}

Final answer:

{answer}
""".strip()


def demonstration_with_reasoning_answer_prompt(
    question: str,
    texts: Sequence[str],
    demonstrations: Sequence[DemonstrationWithReasoning],
):
    examples = format_multi(
        DEMONSTRATION_WITH_REASONING_EXAMPLE,
        [d.as_dict() for d in demonstrations]
        + [dict(question=question, texts=numbered_list(texts), reasoning=stop(""))],
    )
    return "\n\n".join(
        [FEW_SHOT_INSTRUCTIONS + REASONING_ADDITIONAL, "\n\n---\n\n".join(examples)]
    )


SUPPRESS_EOT = {"50256": -100}


async def demonstration_answer(
    question: str, texts: Sequence[str], demonstrations: Sequence[Demonstration]
):
    prompt = demonstration_answer_prompt(question, texts, demonstrations)
    return await recipe.agent().complete(prompt=prompt, stop="\n\n---")


async def demonstration_answer_with_reasoning(
    question: str, texts: Sequence[str], demonstrations: Sequence[Demonstration]
):
    with_reasoning = await add_reasoning(demonstrations)
    prompt = demonstration_with_reasoning_answer_prompt(
        question=question, texts=texts, demonstrations=with_reasoning
    )
    max_tokens = 500
    while True:
        completion = await openai_complete(
            prompt=prompt,
            stop="\n\n---",
            max_tokens=max_tokens,
            logit_bias=SUPPRESS_EOT,
        )
        try:
            answer = completion["choices"][0]["text"].split("Final answer:")[1].strip()
            break
        except IndexError:
            finish_reason = completion["choices"][0]["finish_reason"]
            if finish_reason == "length" and max_tokens < 1_500:
                max_tokens += 200
            else:
                raise

    return answer


recipe.main(simple_answer)
