from dataclasses import dataclass
from typing import Protocol

from ice.recipes.primer.answer_by_computation import answer_by_computation
from ice.recipes.primer.answer_by_reasoning import answer_by_reasoning
from ice.recipes.primer.answer_by_search import answer_by_search


class QuestionRecipe(Protocol):
    async def __call__(self, question: str) -> str:
        ...


@dataclass
class Action:
    name: str
    description: str
    recipe: QuestionRecipe


action_types = [
    Action(
        name="Web search",
        description="Run a web search using Google. This is helpful if the question depends on obscure facts or current information, such as the weather or the latest news.",
        recipe=answer_by_search,
    ),
    Action(
        name="Computation",
        description="Run a computation in Python. This is helpful if the question depends on calculation or other mechanical processes that you can specify in a short program.",
        recipe=answer_by_computation,
    ),
    Action(
        name="Reasoning",
        description="Write out the reasoning steps. This is helpful if the question involves logical deduction or evidence-based reasoning.",
        recipe=answer_by_reasoning,
    ),
]
