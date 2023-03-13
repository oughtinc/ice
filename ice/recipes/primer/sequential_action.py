import math  # noqa: F401
from abc import ABC
from abc import abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Optional

from fvalues import F

from ice.recipe import recipe
from ice.recipes.primer.search_string import search_string


Log = list[str]


def render_enumerate(items: Sequence[object]) -> str:
    """Render numbered list, one per line"""
    return F("\n\n").join(F(f"{i+1}. {item}") for i, item in enumerate(items))


def render_context(question: str, log: Log) -> str:
    question_context = F(f'The question you want to answer: "{question}"')
    if not log:
        return question_context
    return F(
        f"""{question_context}

What you've done so far:

{render_enumerate(log)}"""
    )


def render_action_context(question: str, log: Log, max_actions: int) -> str:
    action_count_text = (
        "You have one action left. (The one you're taking right now.)"
        if max_actions == 1
        else F(
            f"You have {max_actions} actions left. (The one you're taking right now, and {max_actions - 1} follow-up actions.)"
        )
    )
    return F(
        f"""{render_context(question, log)}

{action_count_text}"""
    )


def make_knowledge_prompt(question: str, log: Log) -> str:
    return F(
        f"""{render_context(question, log)}

Q: Do you have enough information to correctly answer the question? Say "A: Yes" or "A: No"
A:"""
    )


def make_answer_prompt(question: str, log: Log) -> str:
    return F(
        f"""{render_context(question, log)}

Q: {question}
A:"""
    )


async def is_info_sufficient(question: str, log: Log) -> bool:
    knowledge_prompt = make_knowledge_prompt(question, log)
    has_knowledge_probs, _ = await recipe.agent().classify(
        prompt=knowledge_prompt, choices=(" Yes", " No")
    )
    return has_knowledge_probs.get(" Yes", 0.0) > 0.7


async def answer_directly(question: str, log: Log) -> str:
    answer_prompt = make_answer_prompt(question, log)
    answer = await recipe.agent("instruct-reasoning").complete(prompt=answer_prompt)
    return answer


class Action(ABC):
    @classmethod
    @abstractmethod
    async def propose(cls, question: str, log: Log, max_actions: int) -> "Action":
        ...

    @abstractmethod
    def run(self):
        ...

    @abstractmethod
    def make_log_entry(self, result: str) -> str:
        ...


@dataclass
class CalculationAction(Action):
    calculation: str

    @classmethod
    def make_proposal_prompt(cls, question: str, log: Log, max_actions: int) -> str:
        return F(
            f"""{render_action_context(question, log, max_actions)}

You have chosen to take the action "Do a calculation".

You have access to a Python interpreter. What single-line calculation would most help you answer the question "{question}"?

>>> import math
>>>"""
        )

    @classmethod
    async def propose(
        cls, question: str, log: Log, max_actions: int
    ) -> "CalculationAction":
        calculation_prompt = cls.make_proposal_prompt(question, log, max_actions)
        calculation = await recipe.agent("instruct-reasoning").complete(
            prompt=calculation_prompt, stop="\n"
        )
        return cls(calculation)

    async def run(self) -> str:
        try:
            return str(eval(self.calculation))
        except Exception as e:
            return F(f"Error: {e}")

    def make_log_entry(self, result: str) -> str:
        return F(f"You calculated '{self.calculation}' and got the result '{result}'.")

    def __str__(self):
        return F(f"Do calculation: {self.calculation}")


@dataclass
class WebSearchAction(Action):
    search_term: str

    @classmethod
    def make_proposal_prompt(cls, question: str, log: Log, max_actions: int) -> str:
        return F(
            f"""{render_action_context(question, log, max_actions)}

You have chosen to take the action "Run a web search".

What is a first web search query you could run to help you answer the question "{question}"?

Query:"""
        )

    @classmethod
    async def propose(
        cls, question: str, log: Log, max_actions: int
    ) -> "WebSearchAction":
        search_term_prompt = cls.make_proposal_prompt(question, log, max_actions)
        search_term = await recipe.agent("instruct-reasoning").complete(
            prompt=search_term_prompt, stop='"'
        )
        return cls(search_term)

    async def run(self) -> str:
        results_str = await search_string(self.search_term)
        return results_str

    def make_log_entry(self, result: str) -> str:
        return F(
            f"You searched the web for '{self.search_term}' and got the result '{result}'."
        )

    def __str__(self):
        return F(f"Run web search: {self.search_term}")


async def get_action_candidates(
    question: str, log: Log, max_actions: int
) -> list[Action]:
    calculation_action = await CalculationAction.propose(question, log, max_actions)
    websearch_action = await WebSearchAction.propose(question, log, max_actions)
    return [calculation_action, websearch_action]


def render_numbers(n: int) -> str:
    numbers = ", ".join(str(i) for i in range(1, n))
    return "{} or {}".format(numbers, n) if n > 1 else str(n)


def make_action_choice_prompt(
    question: str, log: Log, actions: list[Action], max_actions: int
) -> str:
    follow_up_text = (
        ""
        if max_actions == 1
        else F(f", and {max_actions - 1} similar follow-up actions")
    )

    return F(
        f"""{render_context(question, log)}

You can take one of the following actions now{follow_up_text} before you need to answer:

{render_enumerate(actions)}

Question: What next action should you take to make progress on answering the question "{question}"? {render_numbers(len(actions))}?
Answer:"""
    )


async def choose_action(
    question: str, log: Log, actions: list[Action], max_actions
) -> Action:
    action_choice_prompt = make_action_choice_prompt(
        question, log, actions, max_actions
    )
    action_choice_probs = await get_action_choice_probs(action_choice_prompt, actions)
    best_action_index = get_best_action_index(action_choice_probs)
    return actions[best_action_index]


async def get_action_choice_probs(action_choice_prompt, actions):
    action_choice_probs, _ = await recipe.agent("instruct-reasoning-crowd").classify(
        prompt=action_choice_prompt,
        choices=tuple(F(f" {i}") for i in range(1, len(actions) + 1)),
    )
    return action_choice_probs


def get_best_action_index(action_choice_probs):
    best_action_index = None
    best_action_prob = 0
    for action_index, action_prob in action_choice_probs.items():
        if action_prob > best_action_prob:
            best_action_index = int(action_index.strip())
            best_action_prob = action_prob
    assert best_action_index is not None
    return best_action_index - 1


async def gather_info(
    *,
    question: str,
    log: Optional[Log] = None,
    max_actions: int = 3,
) -> Log:
    if log is None:
        log = []
    actions = await get_action_candidates(question, log, max_actions)
    chosen_action = await choose_action(question, log, actions, max_actions)
    result = await chosen_action.run()
    return log + [chosen_action.make_log_entry(result)]


async def sequential_action(
    *,
    question: str = "How far would all the film frames that make up the 400-plus episodes of The Simpsons stretch?",
    max_actions: int = 3,
):
    log: list[str] = []

    for actions_left in range(max_actions, 0, -1):
        sufficient_info = await is_info_sufficient(question, log)
        if sufficient_info:
            break

        log = await gather_info(
            question=question,
            log=log,
            max_actions=actions_left,
        )

    answer = await answer_directly(question, log)

    return answer


recipe.main(sequential_action)
