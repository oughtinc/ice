from ice.agents.base import Agent
from ice.recipe import recipe
from ice.recipes.primer.debate.prompt import *

async def debate(question: str = "Should we ban guns?", agent_names: tuple[Name, Name] = ("Alice", "Bob"), number_of_turns: int = 10):
    debate_history = initialize_debate(question, agent_names)
    for i in range(number_of_turns):
        if i % 2 == 0:
            speaker, listener = agent_names
        else:
            listener, speaker = agent_names
        prompt = render_debate_prompt(speaker, debate_history, number_of_turns-i)
        answer = (await recipe.agent().answer(prompt=prompt)).strip('" ')
        answer = answer.split(listener)[0].strip()
        debate_history.append((speaker, answer))
    return render_debate(debate_history)

recipe.main(debate)