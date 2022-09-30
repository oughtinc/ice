from ice.recipe import recipe
from ice.recipes.primer.answer_by_dispatch.prompt import *


async def answer_by_dispatch(question: str = "How many people live in Germany?"):
    prompt = make_action_selection_prompt(question)
    choices = tuple(str(i) for i in range(1, 6))
    probs, _ = await recipe.agent().classify(prompt=prompt, choices=choices)
    return list(zip(probs.items(), [a.name for a in action_types]))


recipe.main(answer_by_dispatch)
