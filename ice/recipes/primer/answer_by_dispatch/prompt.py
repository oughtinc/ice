from fvalues import F

from ice.recipes.primer.answer_by_dispatch.types import *


def make_action_selection_prompt(question: str) -> str:
    action_types_str = F("\n").join(
        [
            F(f"{i+1}. {action_type.description}")
            for i, action_type in enumerate(action_types)
        ]
    )

    return F(
        f"""You want to answer the question "{question}".

You have the following options:

{action_types_str}

Q: Which of these options do you want to use before you answer the question? Choose the option that will most help you give an accurate answer.
A: I want to use option #"""
    ).strip()
