from collections.abc import Sequence

from structlog.stdlib import get_logger

from ice.recipe import recipe
from ice.recipes.program_search.nodes.augment_question.prompts import EXAMPLE_SEPARATOR
from ice.recipes.program_search.nodes.augment_question.prompts import get_new_questions
from ice.recipes.program_search.nodes.augment_question.prompts import (
    make_augment_question_prompt,
)

log = get_logger()


async def augment_question(
    question: str, current_texts: Sequence[str]
) -> tuple[str, Sequence[str]]:
    """Given a question and some texts, what other questions would be helpful to answer
    to be able to answer the original question completely?

    Args:
        question (str): The original question we are trying to answer
        current_texts (Sequence[str]): Texts we currently have

    Returns:
        tuple[str, Sequence[str]]: The *most important new question, then all new questions
    """
    assert current_texts, "Augment question node not yet designed for 0-text case"
    prompt = make_augment_question_prompt(
        question=question, existing_selections=current_texts
    )
    completion = await recipe.agent().complete(
        prompt=prompt, stop=EXAMPLE_SEPARATOR, max_tokens=312
    )
    return get_new_questions(completion)


recipe.main(augment_question)
