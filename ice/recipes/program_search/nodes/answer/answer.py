from collections.abc import Sequence

from structlog.stdlib import get_logger

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

log = get_logger()

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


async def _get_reasoning(initial_prompt: str, completion: str):
    try:
        return completion.split("Final answer:")[1].strip()
    except IndexError:
        lines = completion.splitlines()
        if not len(lines) == 1:
            raise ValueError("Unexpected response")
        new_prompt = initial_prompt + " " + lines[0].strip() + "\n\n" + "Final answer:"
        new_completion = await openai_complete(
            prompt=new_prompt, stop="\n\n---", max_tokens=200
        )
        log.warning(
            "Final answer not included in initial response",
            initial_response=completion,
            initial_prompt=initial_prompt,
            new_prompt=new_prompt,
            new_final_answer=new_completion,
        )
    return new_completion["choices"][0]["text"].strip()


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
        )
        try:
            answer: str = completion["choices"][0]["text"]
            break
        except IndexError:
            finish_reason = completion["choices"][0]["finish_reason"]
            if finish_reason == "length" and max_tokens < 1_500:
                max_tokens += 200
            else:
                raise

    return await _get_reasoning(prompt, answer)


async def elicit_answer_prompt(question: str, text: str) -> str:
    prompt = f"""Answer the question "{question}" based on the excerpt from a research paper. \
Include everything that the paper excerpt has to say about the answer. \
Make sure everything you say is supported by the excerpt. \
The excerpt may cite other papers; \
answer about the paper you're reading the excerpt from, not the papers that it cites. \
Answer in one phrase or sentence:

Paper excerpt: {text}

Question: {question}

Answer:"""
    completion = await openai_complete(
        prompt=prompt,
        stop=None,
        max_tokens=200,
        model="text-davinci-003",
    )

    return completion["choices"][0]["text"]


recipe.main(simple_answer)
