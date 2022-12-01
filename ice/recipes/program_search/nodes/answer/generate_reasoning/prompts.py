from collections.abc import Sequence

from more_itertools import circular_shifts

from ice.formatter.multi import format_multi
from ice.recipe import recipe
from ice.recipes.program_search.nodes.answer.types import Demonstration
from ice.recipes.program_search.nodes.answer.types import DemonstrationWithReasoning


INSTRUCTIONS = "My friend came up with the following correct answers for each question but didn't write out his reasoning that supports each answer. Can you write a paragraph explaining why each answer is correct? Be sure to quote the parts of the text that support the answer, explaining why this is the correct conclusion."

DEMONSTRATION_EXAMPLE = """

Question: {question}

Text that contains the answer:

{texts}

Correct answer to the question: {answer}

""".strip()

PRE_GENERATION = """

Starting with the first question, {question}, provide a paragraph of reasoning that supports the answer based on the following excerpts, being sure to quote the parts of the excerpts that support the answer and explaining why they support the answer. Only include information that is relevant to answering the question.

{texts}

Let's think it over: First, Excerpt 1 says that""".strip()


def make_reasoning_prompt(demonstrations: Sequence[Demonstration]) -> str:
    examples = format_multi(
        DEMONSTRATION_EXAMPLE, [d.as_dict() for d in demonstrations]
    )
    first_example = demonstrations[0].as_dict()
    return "\n\n".join(
        [
            INSTRUCTIONS,
            "\n\n---\n\n".join(examples),
            PRE_GENERATION.format(
                question=first_example["question"],
                texts=first_example["texts"].transform(),
            ),
        ]
    )


async def add_reasoning(
    demonstrations: Sequence[Demonstration],
) -> Sequence[DemonstrationWithReasoning]:
    shifts = circular_shifts(demonstrations)
    prompts = [make_reasoning_prompt(shift) for shift in shifts]

    async def answer_for_prompt(prompt: str):
        return await recipe.agent().complete(prompt=prompt, stop="\n\n")

    completions = [(await answer_for_prompt(prompt)) for prompt in prompts]

    return [
        DemonstrationWithReasoning(
            reasoning=reasoning, question=d.question, texts=d.texts, answer=d.answer
        )
        for reasoning, d in zip(completions, demonstrations)
    ]


recipe.main(add_reasoning)
