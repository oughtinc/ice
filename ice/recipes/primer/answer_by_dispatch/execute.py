from ice.recipe import recipe
from ice.recipes.primer.answer_by_dispatch.prompt import *


async def select_action(question: str) -> Action:
    prompt = make_action_selection_prompt(question)
    choices = tuple(str(i) for i in range(1, 6))
    choice_probs, _ = await recipe.agent().classify(prompt=prompt, choices=choices)
    best_choice = max(choice_probs.items(), key=lambda x: x[1])[0]
    return action_types[int(best_choice) - 1]


async def answer_by_dispatch(question: str = "How many people live in Germany?") -> str:
    action = await select_action(question)
    result = await action.recipe(question=question)
    return result


recipe.main(answer_by_dispatch)
